"""
Data loader module for caching the TruckChargingSiteSelector instance.
Precomputes scores on first load to improve dashboard performance.
"""

import logging
import geopandas as gpd
from selector import TruckChargingSiteSelector
import pandas as pd
logger = logging.getLogger(__name__)

# Global cache for the selector instance
_selector_cache = None


# Add to top of file
_scored_data_cache = None
_optimal_sites_cache = None

def cache_analysis_results(scored_gdf, optimal_gdf):
    """Cache analysis results in memory (not JSON)"""
    global _scored_data_cache, _optimal_sites_cache
    _scored_data_cache = scored_gdf
    _optimal_sites_cache = optimal_gdf
    logger.info(f"Cached {len(scored_gdf)} scored tracts and {len(optimal_gdf)} optimal sites")

def get_scored_data():
    """Get cached scored data"""
    return _scored_data_cache

def get_optimal_sites():
    """Get cached optimal sites"""
    return _optimal_sites_cache


def get_selector(geojson_path: str = "data/my_data.geojson") -> TruckChargingSiteSelector:
    """
    Returns a cached instance of TruckChargingSiteSelector.
    
    On first call, initializes the selector and precomputes composite scores
    with default weights. Subsequent calls return the cached instance.
    
    Args:
        geojson_path: Path to the main GeoJSON data file
        
    Returns:
        TruckChargingSiteSelector instance with precomputed scores
        
    Note:
        First load may take 20-40 seconds depending on data size.
        The selector's calculate_composite_score() will be called again
        in callbacks when users change weights, which is fast since data
        is already loaded.
    """
    global _selector_cache
    
    if _selector_cache is None:
        logger.info("=" * 60)
        logger.info("Initializing TruckChargingSiteSelector (first load)")
        logger.info(f"Data path: {geojson_path}")
        logger.info("=" * 60)
        
        try:
            # Initialize selector with data
            _selector_cache = TruckChargingSiteSelector(geojson_path)
            logger.info("✓ Selector initialized successfully")
            
            # Precompute scores with default weights
            logger.info("Precomputing composite scores with default weights...")
            logger.info("This may take 20-40 seconds on first load...")
            
            _selector_cache.calculate_composite_score()
            
            logger.info("✓ Composite scores calculated and cached")
            logger.info("=" * 60)
            logger.info("Dashboard ready! Selector loaded in memory.")
            logger.info("=" * 60)
            
        except FileNotFoundError:
            logger.error(f"ERROR: Data file not found at {geojson_path}")
            logger.error("Please ensure your data file exists at the specified path")
            raise
        except Exception as e:
            logger.error(f"ERROR: Failed to initialize selector: {e}", exc_info=True)
            raise
    
    return _selector_cache


def reset_selector_cache():
    """
    Reset the cached selector instance.
    
    Useful for testing or if you need to reload data from disk.
    Note: This will require re-initialization on next get_selector() call.
    """
    global _selector_cache
    _selector_cache = None
    logger.info("Selector cache cleared")


def is_selector_cached() -> bool:
    """
    Check if selector is already cached in memory.
    
    Returns:
        True if selector is cached, False otherwise
    """
    return _selector_cache is not None
    


# Add these global variables at the top with other caches
_truck_chargers_cache = None

def get_truck_chargers(shp_path: str = "data/Electric_Vehicle_Charging_Stations.shp"):
    """
    Load heavy/medium-duty truck charging station locations.
    
    Returns:
        GeoDataFrame with truck charger locations
    """
    global _truck_chargers_cache
    
    if _truck_chargers_cache is None:
        try:
            logger.info("Loading truck charger locations...")
            
            # Read CSV
            gdf = gpd.read_file(shp_path)
            
            # # Create GeoDataFrame from lat/lon
            # gdf = gpd.GeoDataFrame(
            #     df,
            #     geometry=gpd.points_from_xy(df['Longitude'], df['Latitude']),
            #     crs='EPSG:4326'
            # )
            
            # Clean up column names and keep only relevant columns
            # gdf = gdf.rename(columns={
            #     'Station Name': 'name',
            #     'Street Address': 'address',
            #     'City': 'city',
            #     'State': 'state',
            #     'ZIP': 'zip',
            #     'EV Level2 EVSE Num': 'level2_ports',
            #     'EV DC Fast Count': 'dcfc_ports',
            #     'Access Days Time': 'hours',
            #     'EV Pricing': 'pricing',
            #     'Latitude': 'lat',
            #     'Longitude': 'lon'
            # })
            
            # Select relevant columns
            cols_to_keep = ['id', 'city', 'state', 'zip', 'geometry']
            gdf = gdf[[col for col in cols_to_keep if col in gdf.columns]]
            
            _truck_chargers_cache = gdf
            logger.info(f"✓ Loaded {len(gdf)} truck charging stations")
            
        except FileNotFoundError:
            logger.warning(f"Truck charger file not found at {shp_path}")
            _truck_chargers_cache = gpd.GeoDataFrame()
        except Exception as e:
            logger.error(f"Error loading truck chargers: {e}", exc_info=True)
            _truck_chargers_cache = gpd.GeoDataFrame()
    
    return _truck_chargers_cache