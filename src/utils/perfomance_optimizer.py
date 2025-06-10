# src/utils/performance_optimizer.py
"""
Performance optimization and caching system for Physics Literature Synthesis Pipeline
Implements intelligent caching, background processing, and memory optimization
"""

import asyncio
import threading
import time
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
from datetime import datetime, timedelta
import json
import hashlib
from functools import wraps
import gc
import sys

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class PerformanceCache:
    """
    Intelligent caching system with TTL and memory management
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize performance cache
        
        Args:
            max_size: Maximum number of cached items
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache = {}
        self._access_times = {}
        self._expire_times = {}
        self._lock = threading.RLock()
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        
        logger.info(f"PerformanceCache initialized: max_size={max_size}, ttl={default_ttl}s")
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self._lock:
            current_time = time.time()
            
            if key not in self._cache:
                return None
            
            # Check if expired
            if current_time > self._expire_times[key]:
                self._remove_key(key)
                return None
            
            # Update access time
            self._access_times[key] = current_time
            return self._cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set item in cache"""
        with self._lock:
            current_time = time.time()
            
            # Use default TTL if not specified
            ttl = ttl or self.default_ttl
            
            # Evict if cache is full
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()
            
            # Store item
            self._cache[key] = value
            self._access_times[key] = current_time
            self._expire_times[key] = current_time + ttl
    
    def delete(self, key: str) -> bool:
        """Delete item from cache"""
        with self._lock:
            if key in self._cache:
                self._remove_key(key)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cached items"""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
            self._expire_times.clear()
    
    def _remove_key(self, key: str) -> None:
        """Remove key from all cache structures"""
        self._cache.pop(key, None)
        self._access_times.pop(key, None)
        self._expire_times.pop(key, None)
    
    def _evict_lru(self) -> None:
        """Evict least recently used item"""
        if not self._access_times:
            return
        
        # Find LRU key
        lru_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        self._remove_key(lru_key)
    
    def _cleanup_loop(self) -> None:
        """Background cleanup of expired items"""
        while True:
            try:
                current_time = time.time()
                expired_keys = []
                
                with self._lock:
                    for key, expire_time in self._expire_times.items():
                        if current_time > expire_time:
                            expired_keys.append(key)
                
                # Remove expired keys
                for key in expired_keys:
                    with self._lock:
                        self._remove_key(key)
                
                if expired_keys:
                    logger.debug(f"Cleaned up {len(expired_keys)} expired cache items")
                
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
            
            # Sleep for 5 minutes before next cleanup
            time.sleep(300)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'utilization': len(self._cache) / self.max_size * 100,
                'oldest_item_age': time.time() - min(self._access_times.values()) if self._access_times else 0
            }


class BackgroundProcessor:
    """
    Background task processor for non-blocking operations
    """
    
    def __init__(self, max_workers: int = 2):
        """
        Initialize background processor
        
        Args:
            max_workers: Maximum number of worker threads
        """
        self.max_workers = max_workers
        self._task_queue = []
        self._workers = []
        self._lock = threading.Lock()
        self._shutdown = False
        
        # Start worker threads
        for i in range(max_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self._workers.append(worker)
        
        logger.info(f"BackgroundProcessor initialized with {max_workers} workers")
    
    def submit_task(self, func: Callable, *args, **kwargs) -> None:
        """Submit a task for background processing"""
        if self._shutdown:
            return
        
        task = {
            'func': func,
            'args': args,
            'kwargs': kwargs,
            'submitted_at': time.time()
        }
        
        with self._lock:
            self._task_queue.append(task)
    
    def _worker_loop(self) -> None:
        """Worker thread loop"""
        while not self._shutdown:
            task = None
            
            with self._lock:
                if self._task_queue:
                    task = self._task_queue.pop(0)
            
            if task:
                try:
                    task['func'](*task['args'], **task['kwargs'])
                except Exception as e:
                    logger.error(f"Background task failed: {e}")
            else:
                time.sleep(0.1)  # No tasks, sleep briefly
    
    def shutdown(self) -> None:
        """Shutdown background processor"""
        self._shutdown = True
        for worker in self._workers:
            worker.join(timeout=1)


class MemoryOptimizer:
    """
    Memory optimization utilities
    """
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """Get current memory usage statistics"""
        import psutil
        
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
            'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
            'percent': process.memory_percent(),
            'available_mb': psutil.virtual_memory().available / 1024 / 1024
        }
    
    @staticmethod
    def force_garbage_collection() -> Dict[str, int]:
        """Force garbage collection and return statistics"""
        before_objects = len(gc.get_objects())
        
        # Force collection for all generations
        collected = [gc.collect(generation) for generation in range(3)]
        
        after_objects = len(gc.get_objects())
        
        return {
            'objects_before': before_objects,
            'objects_after': after_objects,
            'objects_collected': before_objects - after_objects,
            'collection_counts': collected
        }
    
    @staticmethod
    def optimize_session_data(session_data: Dict) -> Dict:
        """Optimize session data for memory efficiency"""
        optimized = session_data.copy()
        
        # Compress message content if very long
        if 'messages' in optimized:
            for message in optimized['messages']:
                if len(message.get('content', '')) > 10000:
                    # Keep first and last parts, indicate truncation
                    content = message['content']
                    message['content'] = content[:5000] + "\n\n[... content truncated ...]\n\n" + content[-2000:]
        
        return optimized


class PerformanceOptimizer:
    """
    Main performance optimization coordinator
    """
    
    def __init__(self, cache_size: int = 1000, workers: int = 2):
        """
        Initialize performance optimizer
        
        Args:
            cache_size: Size of performance cache
            workers: Number of background workers
        """
        self.cache = PerformanceCache(max_size=cache_size)
        self.background_processor = BackgroundProcessor(max_workers=workers)
        self.memory_optimizer = MemoryOptimizer()
        
        # Performance metrics
        self._metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'background_tasks': 0,
            'optimizations_run': 0
        }
        
        logger.info("PerformanceOptimizer initialized")
    
    def cached_call(self, cache_key: str, func: Callable, *args, ttl: Optional[int] = None, **kwargs) -> Any:
        """
        Execute function with caching
        
        Args:
            cache_key: Unique cache key
            func: Function to execute
            ttl: Cache time-to-live
            *args, **kwargs: Function arguments
            
        Returns:
            Function result (cached or fresh)
        """
        # Try cache first
        result = self.cache.get(cache_key)
        if result is not None:
            self._metrics['cache_hits'] += 1
            return result
        
        # Cache miss - execute function
        self._metrics['cache_misses'] += 1
        result = func(*args, **kwargs)
        
        # Cache result
        self.cache.set(cache_key, result, ttl)
        
        return result
    
    def background_optimize(self, func: Callable, *args, **kwargs) -> None:
        """Submit optimization task for background processing"""
        self._metrics['background_tasks'] += 1
        self.background_processor.submit_task(func, *args, **kwargs)
    
    def optimize_memory(self) -> Dict[str, Any]:
        """Run memory optimization"""
        self._metrics['optimizations_run'] += 1
        
        before_memory = self.memory_optimizer.get_memory_usage()
        gc_stats = self.memory_optimizer.force_garbage_collection()
        after_memory = self.memory_optimizer.get_memory_usage()
        
        memory_saved = before_memory['rss_mb'] - after_memory['rss_mb']
        
        logger.info(f"Memory optimization: {memory_saved:.2f}MB saved, {gc_stats['objects_collected']} objects collected")
        
        return {
            'memory_saved_mb': memory_saved,
            'before_memory': before_memory,
            'after_memory': after_memory,
            'gc_stats': gc_stats
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        cache_stats = self.cache.get_stats()
        memory_stats = self.memory_optimizer.get_memory_usage()
        
        cache_hit_rate = 0
        if self._metrics['cache_hits'] + self._metrics['cache_misses'] > 0:
            cache_hit_rate = self._metrics['cache_hits'] / (self._metrics['cache_hits'] + self._metrics['cache_misses']) * 100
        
        return {
            'cache': {
                'stats': cache_stats,
                'hit_rate': cache_hit_rate,
                'total_hits': self._metrics['cache_hits'],
                'total_misses': self._metrics['cache_misses']
            },
            'memory': memory_stats,
            'background_tasks': self._metrics['background_tasks'],
            'optimizations_run': self._metrics['optimizations_run']
        }
    
    def shutdown(self) -> None:
        """Shutdown performance optimizer"""
        self.background_processor.shutdown()
        self.cache.clear()


# Global performance optimizer instance
_global_optimizer = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """Get global performance optimizer instance"""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = PerformanceOptimizer()
    return _global_optimizer


def performance_cached(cache_key_func: Optional[Callable] = None, ttl: int = 3600):
    """
    Decorator for caching function results
    
    Args:
        cache_key_func: Function to generate cache key (optional)
        ttl: Cache time-to-live in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            optimizer = get_performance_optimizer()
            
            # Generate cache key
            if cache_key_func:
                cache_key = cache_key_func(*args, **kwargs)
            else:
                # Default key generation
                key_data = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
                cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            return optimizer.cached_call(cache_key, func, *args, ttl=ttl, **kwargs)
        
        return wrapper
    return decorator


def background_task(func):
    """Decorator for submitting functions as background tasks"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        optimizer = get_performance_optimizer()
        optimizer.background_optimize(func, *args, **kwargs)
    
    return wrapper


class SessionPerformanceTracker:
    """
    Track performance metrics for session operations
    """
    
    def __init__(self):
        self.operation_times = {}
        self.operation_counts = {}
    
    def time_operation(self, operation_name: str):
        """Context manager for timing operations"""
        return self._OperationTimer(self, operation_name)
    
    def record_operation(self, operation_name: str, duration: float):
        """Record operation timing"""
        if operation_name not in self.operation_times:
            self.operation_times[operation_name] = []
            self.operation_counts[operation_name] = 0
        
        self.operation_times[operation_name].append(duration)
        self.operation_counts[operation_name] += 1
        
        # Keep only last 100 measurements
        if len(self.operation_times[operation_name]) > 100:
            self.operation_times[operation_name] = self.operation_times[operation_name][-100:]
    
    def get_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics"""
        stats = {}
        
        for operation, times in self.operation_times.items():
            if times:
                stats[operation] = {
                    'count': self.operation_counts[operation],
                    'avg_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'total_time': sum(times)
                }
        
        return stats
    
    class _OperationTimer:
        def __init__(self, tracker, operation_name):
            self.tracker = tracker
            self.operation_name = operation_name
            self.start_time = None
        
        def __enter__(self):
            self.start_time = time.time()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start_time
            self.tracker.record_operation(self.operation_name, duration)


# Global performance tracker
_global_tracker = SessionPerformanceTracker()


def get_performance_tracker() -> SessionPerformanceTracker:
    """Get global performance tracker"""
    return _global_tracker