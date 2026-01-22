"""
GeoJSON file loader with error handling and optimization
"""
import requests
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def load_geojson(url: str, timeout: int = 120) -> Dict[str, Any]:
    """
    Load GeoJSON from URL with proper error handling
    
    Args:
        url: URL to fetch GeoJSON from
        timeout: Request timeout in seconds
        
    Returns:
        Parsed GeoJSON dictionary
        
    Raises:
        Exception: If loading fails
    """
    logger.info(f"Loading GeoJSON from: {url}")
    
    try:
        # Stream the download for large files
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # Get file size if available
        content_length = response.headers.get('content-length')
        if content_length:
            size_mb = int(content_length) / (1024 * 1024)
            logger.info(f"File size: {size_mb:.2f} MB")
        
        # Load JSON
        logger.info("Parsing GeoJSON...")
        data = response.json()
        
        # Validate structure
        if not isinstance(data, dict):
            raise ValueError("Invalid GeoJSON: root must be an object")
        
        if 'type' not in data:
            raise ValueError("Invalid GeoJSON: missing 'type' field")
        
        # Log statistics
        if 'features' in data:
            feature_count = len(data['features'])
            logger.info(f"Loaded {feature_count} features successfully")
        
        return data
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout loading GeoJSON from {url}")
        raise Exception(f"Request timed out after {timeout} seconds")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        raise Exception(f"Failed to fetch GeoJSON: {str(e)}")
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        raise Exception(f"Invalid JSON format: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error loading GeoJSON: {e}")
        raise


def get_empty_geojson() -> Dict[str, Any]:
    """Return empty GeoJSON structure as fallback"""
    return {
        "type": "FeatureCollection",
        "features": []
    }