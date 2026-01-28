# SPDX-FileCopyrightText: 2025-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

import hashlib
import magic

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# Allowed file types for paper submissions
ALLOWED_PAPER_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
    'application/vnd.oasis.opendocument.text',  # .odt
    'text/plain',
    'application/x-latex',
    'application/x-tex',
]

# Maximum file sizes (in bytes)
MAX_PAPER_SIZE = 25 * 1024 * 1024  # 25 MB
MAX_IMAGE_SIZE = 5 * 1024 * 1024   # 5 MB


def validate_file_type(file, allowed_types=None):
    """
    Validate file type using python-magic for accurate MIME type detection.
    
    :param file: The uploaded file object
    :param allowed_types: List of allowed MIME types (defaults to ALLOWED_PAPER_TYPES)
    :raises ValidationError: If file type is not allowed
    """
    if allowed_types is None:
        allowed_types = ALLOWED_PAPER_TYPES
    
    # Read file content for validation
    file.seek(0)
    file_content = file.read(2048)  # Read first 2KB for type detection
    file.seek(0)  # Reset file pointer
    
    # Detect MIME type using magic
    try:
        mime = magic.from_buffer(file_content, mime=True)
    except Exception:
        # Fallback to file extension if magic fails
        mime = file.content_type
    
    if mime not in allowed_types:
        allowed_extensions = [
            '.pdf', '.doc', '.docx', '.odt', '.txt', '.tex', '.latex'
        ]
        raise ValidationError(
            _(
                'Unsupported file type: %(mime)s. Allowed types are: %(types)s'
            ) % {
                'mime': mime,
                'types': ', '.join(allowed_extensions)
            }
        )
    
    return mime


def validate_file_size(file, max_size=None):
    """
    Validate file size.
    
    :param file: The uploaded file object
    :param max_size: Maximum file size in bytes (defaults to MAX_PAPER_SIZE)
    :raises ValidationError: If file is too large
    """
    if max_size is None:
        max_size = MAX_PAPER_SIZE
    
    file.seek(0, 2)  # Seek to end of file
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    
    if file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        actual_size_mb = file_size / (1024 * 1024)
        raise ValidationError(
            _(
                'File size (%(actual)s MB) exceeds maximum allowed size of %(max)s MB.'
            ) % {
                'actual': f'{actual_size_mb:.2f}',
                'max': f'{max_size_mb:.0f}'
            }
        )
    
    return file_size


def calculate_file_hash(file, algorithm='sha256'):
    """
    Calculate hash of file content for integrity verification.
    
    :param file: The uploaded file object
    :param algorithm: Hash algorithm to use (sha256, sha1, md5)
    :return: Hexadecimal hash string
    """
    file.seek(0)
    
    if algorithm == 'sha256':
        hasher = hashlib.sha256()
    elif algorithm == 'sha1':
        hasher = hashlib.sha1()
    elif algorithm == 'md5':
        hasher = hashlib.md5()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    # Read file in chunks to handle large files
    for chunk in iter(lambda: file.read(8192), b''):
        hasher.update(chunk)
    
    file.seek(0)  # Reset file pointer
    return hasher.hexdigest()


def validate_paper_upload(file):
    """
    Comprehensive validation for paper uploads.
    
    Performs:
    - File type validation
    - File size validation
    - Calculates file hash for integrity
    
    :param file: The uploaded file object
    :return: Dictionary with validation results and metadata
    :raises ValidationError: If validation fails
    """
    # Validate file type
    mime_type = validate_file_type(file, ALLOWED_PAPER_TYPES)
    
    # Validate file size
    file_size = validate_file_size(file, MAX_PAPER_SIZE)
    
    # Calculate file hash
    file_hash = calculate_file_hash(file, 'sha256')
    
    return {
        'mime_type': mime_type,
        'file_size': file_size,
        'file_hash': file_hash,
        'validated': True,
    }


def validate_image_upload(file):
    """
    Validate image uploads.
    
    :param file: The uploaded image file object
    :return: Dictionary with validation results
    :raises ValidationError: If validation fails
    """
    allowed_image_types = [
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp',
        'image/svg+xml',
    ]
    
    # Validate file type
    mime_type = validate_file_type(file, allowed_image_types)
    
    # Validate file size
    file_size = validate_file_size(file, MAX_IMAGE_SIZE)
    
    # Calculate file hash
    file_hash = calculate_file_hash(file, 'sha256')
    
    return {
        'mime_type': mime_type,
        'file_size': file_size,
        'file_hash': file_hash,
        'validated': True,
    }


def check_file_integrity(file, expected_hash, algorithm='sha256'):
    """
    Verify file integrity by comparing with expected hash.
    
    :param file: The file object to check
    :param expected_hash: The expected hash value
    :param algorithm: Hash algorithm used
    :return: True if hash matches, False otherwise
    """
    actual_hash = calculate_file_hash(file, algorithm)
    return actual_hash == expected_hash
