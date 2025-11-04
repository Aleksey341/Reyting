from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import logging
import hashlib
from datetime import datetime

from database import get_db
from models import UploadLog, SrcRegistry

router = APIRouter()
logger = logging.getLogger(__name__)


async def calculate_file_hash(file_content: bytes) -> str:
    """Calculate SHA256 hash of file content"""
    return hashlib.sha256(file_content).hexdigest()


@router.post("/{source_id}")
async def upload_file(
    source_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload data file from source.
    Supports CSV, Excel, and other formats.
    """
    try:
        # Check source exists
        source = db.query(SrcRegistry).filter(
            SrcRegistry.source_id == source_id
        ).first()

        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        # Read file
        content = await file.read()
        file_hash = await calculate_file_hash(content)

        # Create upload log entry
        upload_log = UploadLog(
            source_id=source_id,
            file_name=file.filename,
            file_hash=file_hash,
            records_count=0,
            status="pending",
            uploaded_at=datetime.utcnow(),
        )

        db.add(upload_log)
        db.commit()
        db.refresh(upload_log)

        logger.info(
            f"File uploaded: {file.filename} (source_id={source_id}, upload_id={upload_log.upload_id})"
        )

        return {
            "status": "success",
            "upload_id": upload_log.upload_id,
            "file_name": file.filename,
            "file_hash": file_hash,
            "source_id": source_id,
            "message": "File received and queued for processing",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail="Error uploading file")


@router.get("/uploads/{upload_id}")
async def get_upload_status(
    upload_id: int,
    db: Session = Depends(get_db),
):
    """Get status of a previous upload"""
    try:
        upload = db.query(UploadLog).filter(
            UploadLog.upload_id == upload_id
        ).first()

        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")

        return {
            "status": "success",
            "upload_id": upload.upload_id,
            "file_name": upload.file_name,
            "upload_status": upload.status,
            "records_count": upload.records_count,
            "error_message": upload.error_message,
            "uploaded_at": upload.uploaded_at.isoformat() if upload.uploaded_at else None,
            "processed_at": upload.processed_at.isoformat() if upload.processed_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching upload status: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching upload status")
