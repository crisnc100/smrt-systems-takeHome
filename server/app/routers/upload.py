from typing import Optional, Dict
import os
import io
import zipfile

from fastapi import APIRouter, UploadFile, File, HTTPException

from ..engine import duck


router = APIRouter(prefix="/datasource", tags=["datasource"])


def _save_file(dst_path: str, upload: UploadFile) -> None:
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    with open(dst_path, "wb") as f:
        f.write(upload.file.read())


def _normalize_name(name: str) -> str:
    # Strip directories and normalize case/extension
    base = os.path.basename(name)
    base = base.lower()
    return base


def _extract_from_zip(content: bytes) -> Dict[str, bytes]:
    files: Dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = _normalize_name(info.filename)
            with zf.open(info) as fp:
                files[name] = fp.read()
    return files


@router.post("/upload")
async def upload_csv(
    customer: Optional[UploadFile] = File(default=None),
    inventory: Optional[UploadFile] = File(default=None),
    detail: Optional[UploadFile] = File(default=None),
    pricelist: Optional[UploadFile] = File(default=None),
    zip: Optional[UploadFile] = File(default=None),  # optional zip containing the four CSVs
    alias_map: Optional[UploadFile] = File(default=None),  # optional alias_map.json
):
    """
    Upload CSVs (or a ZIP of them) and refresh the in-memory views.

    Accepted inputs:
    - Individual files via fields: customer, inventory, detail, pricelist
    - Or a single `zip` file containing any/all of: Customer.csv, Inventory.csv, Detail.csv, Pricelist.csv
    """
    data_dir = duck.get_data_dir()
    saved_any = False

    # Map canonical filenames we expect
    targets = {
        "customer": os.path.join(data_dir, "Customer.csv"),
        "inventory": os.path.join(data_dir, "Inventory.csv"),
        "detail": os.path.join(data_dir, "Detail.csv"),
        "pricelist": os.path.join(data_dir, "Pricelist.csv"),
    }

    # 1) Save direct uploads if provided
    if customer is not None:
        _save_file(targets["customer"], customer)
        saved_any = True
    if inventory is not None:
        _save_file(targets["inventory"], inventory)
        saved_any = True
    if detail is not None:
        _save_file(targets["detail"], detail)
        saved_any = True
    if pricelist is not None:
        _save_file(targets["pricelist"], pricelist)
        saved_any = True

    # Save alias map if provided directly
    if alias_map is not None:
        alias_path = os.path.join(data_dir, "alias_map.json")
        _save_file(alias_path, alias_map)
        saved_any = True

    # 2) If a zip is provided, extract supported files
    if zip is not None:
        content = await zip.read()
        try:
            extracted = _extract_from_zip(content)
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Invalid ZIP file")

        # map by filenames regardless of case
        name_map = {k: v for k, v in extracted.items()}
        # Accept common variations
        variants = {
            "customer": ["customer.csv"],
            "inventory": ["inventory.csv"],
            "detail": ["detail.csv"],
            "pricelist": ["pricelist.csv"],
        }

        for key, outs in [("customer", targets["customer"]), ("inventory", targets["inventory"]), ("detail", targets["detail"]), ("pricelist", targets["pricelist"])]:
            for candidate in variants[key]:
                if candidate in name_map:
                    os.makedirs(os.path.dirname(outs), exist_ok=True)
                    with open(outs, "wb") as f:
                        f.write(name_map[candidate])
                    saved_any = True
                    break
        # Also extract alias_map.json if present
        if "alias_map.json" in name_map:
            alias_path = os.path.join(data_dir, "alias_map.json")
            with open(alias_path, "wb") as f:
                f.write(name_map["alias_map.json"])
            saved_any = True

    if not saved_any:
        raise HTTPException(status_code=400, detail="No files provided. Upload customer/inventory/detail/pricelist CSVs or a ZIP.")

    # Rebuild Parquet cache and views
    built = duck.build_parquet_cache()
    # Force all threads to reload views on next access
    duck.invalidate_all_connections()
    views = duck.ensure_views()
    counts = duck.table_counts()
    duck.clear_cache()

    return {
        "status": "ok",
        "saved": {k: os.path.exists(v) for k, v in targets.items()},
        "parquet_built": built,
        "views": views,
        "counts": counts,
    }
