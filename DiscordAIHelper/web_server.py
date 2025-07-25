
"""
Ultra-Robust Web Server for Discord AI Selfbot
Provides multiple health check endpoints and intensive activity simulation
"""

import asyncio
import time
import random
import json
import threading
import logging
import os
from aiohttp import web
from typing import Dict, Any

logger = logging.getLogger(__name__)

class UltraRobustHealthServer:
    """Ultra-robust health check server with multiple endpoints"""
    
    def __init__(self, port=5000):
        self.port = port
        self.app = None
        self.runner = None
        self.site = None
        self.request_count = 0
        self.start_time = time.time()
        self.active_data = {}
        self.error_count = 0
    
    def generate_intensive_activity(self) -> Dict[str, Any]:
        """Generate intensive computational activity"""
        # Heavy computation to show high CPU usage
        result = sum(i * random.randint(1, 100) for i in range(10000))
        
        # Memory operations
        big_data = [random.random() for _ in range(1000)]
        processed_data = [x * 2 + random.random() for x in big_data]
        
        # Store in memory to keep it active
        current_time = time.time()
        self.active_data[current_time] = {
            'computation_result': result,
            'data_size': len(processed_data),
            'random_values': processed_data[:10],  # Keep sample
            'timestamp': current_time
        }
        
        # Clean old data
        if len(self.active_data) > 50:
            oldest_key = min(self.active_data.keys())
            del self.active_data[oldest_key]
        
        return {
            'computation_cycles': result,
            'data_processed': len(processed_data),
            'memory_objects': len(self.active_data),
            'cpu_intensive': True,
            'memory_active': True
        }
    
    async def health_check(self, request):
        """Enhanced health check endpoint"""
        self.request_count += 1
        
        try:
            # Generate activity
            activity_data = self.generate_intensive_activity()
            
            response = {
                "status": "ultra_healthy_24_7",
                "service": "Discord AI Selfbot",
                "version": "3.0.0",
                "uptime": time.time() - self.start_time,
                "request_count": self.request_count,
                "timestamp": time.time(),
                "active": True,
                "ultra_robust": True,
                "activity": activity_data,
                "error_count": self.error_count
            }
            
            return web.json_response(response)
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Health check error: {e}")
            return web.json_response({
                "status": "error_but_running",
                "error": str(e),
                "timestamp": time.time()
            }, status=500)
    
    async def ultra_activity_endpoint(self, request):
        """Ultra-intensive activity simulation endpoint"""
        try:
            # Even more intensive operations
            heavy_computation = 0
            for i in range(50000):
                heavy_computation += i * random.randint(1, 10)
            
            # File system simulation
            import os
            temp_data = f"ultra_activity_{time.time()}_{random.randint(1000, 9999)}"
            
            # Memory stress test
            memory_test = [random.random() * i for i in range(5000)]
            memory_result = sum(memory_test)
            
            activity_data = self.generate_intensive_activity()
            
            response = {
                "activity": "ultra_extreme_simulation",
                "timestamp": time.time(),
                "heavy_computation": heavy_computation,
                "memory_result": memory_result,
                "memory_objects": len(memory_test),
                "temp_data": temp_data,
                "cpu_stress": True,
                "memory_stress": True,
                "ultra_active": True,
                **activity_data
            }
            
            return web.json_response(response)
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Ultra activity error: {e}")
            return web.json_response({
                "activity": "error_but_active",
                "error": str(e),
                "timestamp": time.time()
            }, status=500)
    
    async def stats_endpoint(self, request):
        """Comprehensive stats endpoint"""
        try:
            uptime = time.time() - self.start_time
            
            response = {
                "uptime_seconds": uptime,
                "uptime_minutes": uptime / 60,
                "uptime_hours": uptime / 3600,
                "total_requests": self.request_count,
                "requests_per_minute": self.request_count / max(uptime / 60, 1),
                "error_count": self.error_count,
                "success_rate": (self.request_count - self.error_count) / max(self.request_count, 1),
                "memory_objects": len(self.active_data),
                "status": "running_24_7_ultra_robust",
                "last_activity": time.time(),
                "active_data_size": len(self.active_data),
                "server_healthy": True
            }
            
            return web.json_response(response)
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Stats endpoint error: {e}")
            return web.json_response({
                "error": str(e),
                "timestamp": time.time()
            }, status=500)
    
    async def ping_endpoint(self, request):
        """Enhanced ping endpoint with computation"""
        try:
            # Quick computation for each ping
            ping_computation = sum(range(random.randint(100, 1000)))
            
            response = {
                "pong": time.time(),
                "ultra": True,
                "computation": ping_computation,
                "request_id": self.request_count,
                "active": True
            }
            
            return web.json_response(response)
            
        except Exception as e:
            self.error_count += 1
            return web.json_response({
                "pong": time.time(),
                "error": str(e)
            }, status=500)
    
    async def stress_endpoint(self, request):
        """Stress test endpoint for maximum activity"""
        try:
            # Maximum stress operations
            stress_results = []
            
            for _ in range(10):
                # Heavy computation
                result = sum(i ** 2 for i in range(1000))
                stress_results.append(result)
                
                # Memory allocation
                temp_memory = [random.random() for _ in range(2000)]
                stress_results.append(len(temp_memory))
            
            # Generate large response
            response = {
                "stress_test": "maximum_load",
                "timestamp": time.time(),
                "stress_results": stress_results,
                "total_operations": len(stress_results),
                "memory_pressure": True,
                "cpu_pressure": True,
                "ultra_stress": True,
                "large_data": [random.randint(1, 10000) for _ in range(100)]
            }
            
            return web.json_response(response)
            
        except Exception as e:
            self.error_count += 1
            return web.json_response({
                "stress_test": "error_but_stressed",
                "error": str(e),
                "timestamp": time.time()
            }, status=500)
    
    async def start_server(self):
        """Start the ultra-robust health check server with port fallback"""
        max_attempts = 10
        base_port = self.port
        
        for attempt in range(max_attempts):
            try:
                current_port = base_port + attempt
                
                self.app = web.Application()
                
                # Add all endpoints
                self.app.router.add_get('/', self.health_check)
                self.app.router.add_get('/health', self.health_check)
                self.app.router.add_get('/activity', self.ultra_activity_endpoint)
                self.app.router.add_get('/stats', self.stats_endpoint)
                self.app.router.add_get('/ping', self.ping_endpoint)
                self.app.router.add_get('/stress', self.stress_endpoint)
                
                # Add POST endpoints for more activity
                self.app.router.add_post('/health', self.health_check)
                self.app.router.add_post('/activity', self.ultra_activity_endpoint)
                self.app.router.add_post('/stress', self.stress_endpoint)
                
                self.runner = web.AppRunner(self.app)
                await self.runner.setup()
                
                self.site = web.TCPSite(self.runner, '0.0.0.0', current_port)
                await self.site.start()
                
                self.port = current_port  # Update port to the one that worked
                logger.info(f"Ultra-robust health server started on port {current_port} (attempt {attempt + 1})")
                return
                
            except OSError as e:
                if "Address already in use" in str(e) and attempt < max_attempts - 1:
                    logger.error(f"Health server startup failed (attempt {attempt + 1}): {e}")
                    if self.runner:
                        try:
                            await self.runner.cleanup()
                        except:
                            pass
                    continue
                else:
                    logger.error(f"Failed to start ultra-robust health server after {attempt + 1} attempts: {e}")
                    raise
            except Exception as e:
                logger.error(f"Failed to start ultra-robust health server: {e}")
                if self.runner:
                    try:
                        await self.runner.cleanup()
                    except:
                        pass
                raise
    
    async def stop_server(self):
        """Stop the health check server"""
        try:
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()
            logger.info("Ultra-robust health server stopped")
        except Exception as e:
            logger.error(f"Error stopping health server: {e}")

# Global health server instance
_health_server = None

async def start_health_server(port=None):
    """Start the ultra-robust health check server"""
    global _health_server
    # Use Render's PORT environment variable if available, otherwise default to 5000
    if port is None:
        port = int(os.getenv('PORT', 5000))
    _health_server = UltraRobustHealthServer(port)
    await _health_server.start_server()

async def stop_health_server():
    """Stop the health check server"""
    global _health_server
    if _health_server:
        await _health_server.stop_server()
        _health_server = None
