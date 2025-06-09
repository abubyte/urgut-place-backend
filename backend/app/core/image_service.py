import os
import uuid
import logging
from fastapi import UploadFile, HTTPException
from PIL import Image
import aiofiles
from typing import List
import shutil
from app.core.s3_service import S3Service
from botocore.exceptions import ClientError

# Set up logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self):
        self.allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        self.max_file_size = 5 * 1024 * 1024  # 5MB
        self.max_dimension = 1920  # Max width/height in pixels
        self.s3_service = S3Service()

    async def save_image(self, file: UploadFile, entity_type: str) -> str:
        """Save an uploaded image and return its path."""
        if not file or not file.filename:
            logger.warning("No file provided or file has no name.")
            return None # Return None if no file is provided or it's empty

        # Validate file extension
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in self.allowed_extensions:
            logger.warning(f"Invalid file type: {file.filename}. Allowed types: {', '.join(self.allowed_extensions)}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(self.allowed_extensions)}"
            )

        # Generate unique filename
        filename = f"{uuid.uuid4()}{ext}"
        temp_path = f"temp_{filename}"
        s3_path = f"{entity_type}/{filename}"

        try:
            # Save file temporarily
            async with aiofiles.open(temp_path, 'wb') as out_file:
                content = await file.read()
                if len(content) == 0:
                    logger.warning(f"Uploaded file is empty: {file.filename}")
                    return None # Return None if the file is empty after reading
                if len(content) > self.max_file_size:
                    raise HTTPException(status_code=400, detail="File too large. Max size: 5MB")
                await out_file.write(content)

            # Process image
            with Image.open(temp_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if too large
                if max(img.size) > self.max_dimension:
                    ratio = self.max_dimension / max(img.size)
                    new_size = tuple(int(dim * ratio) for dim in img.size)
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Save processed image
                img.save(temp_path, quality=85, optimize=True)

            # Upload to S3
            s3_path = await self.s3_service.upload_file(temp_path, s3_path)
            logger.info(f"Successfully uploaded {file.filename} to S3 path: {s3_path}")
            return s3_path

        except ClientError as e:
            logger.error(f"S3 Client Error uploading file {file.filename}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error uploading file to storage") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred while processing file {file.filename}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error processing image") from e
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    async def delete_image(self, image_path: str) -> None:
        """Delete an image file."""
        await self.s3_service.delete_file(image_path)

    async def delete_images(self, image_paths: List[str]) -> None:
        """Delete multiple image files."""
        await self.s3_service.delete_files(image_paths)

    def get_image_url(self, image_path: str) -> str:
        """Get the full URL for an image."""
        if not image_path:
            return None
        return self.s3_service.get_file_url(image_path) 