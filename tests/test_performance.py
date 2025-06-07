"""
Performance and stress tests for e2b-mcp.

This module tests performance characteristics and ensures the library
can handle high load scenarios efficiently.
"""
import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from e2b_mcp import E2BMCPRunner, ServerConfig, Tool, MCPError


# Mark all tests in this module as slow running
pytestmark = pytest.mark.slow


class TestPerformance:
    """Test performance characteristics."""

    def test_server_configuration_performance(self):
        """Test performance of adding many server configurations."""
        runner = E2BMCPRunner(api_key="test_key")
        
        start_time = time.time()
        
        # Add 1000 server configurations
        for i in range(1000):
            config = ServerConfig(
                name=f"server_{i:04d}",
                command=f"python server_{i}.py",
                description=f"Performance test server {i}",
                timeout_minutes=10
            )
            runner.add_server(config)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should be fast (under 1 second for 1000 configs)
        assert duration < 1.0, f"Adding 1000 configs took {duration:.3f}s, expected < 1.0s"
        assert len(runner.list_servers()) == 1000

    def test_bulk_configuration_performance(self):
        """Test performance of bulk server configuration."""
        runner = E2BMCPRunner(api_key="test_key")
        
        # Create bulk configuration
        bulk_config = {}
        for i in range(1000):
            bulk_config[f"server_{i:04d}"] = {
                "command": f"python server_{i}.py",
                "description": f"Bulk test server {i}",
                "timeout_minutes": 10
            }
        
        start_time = time.time()
        runner.add_servers(bulk_config)
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Bulk should be reasonably fast
        assert duration < 2.0, f"Bulk adding 1000 configs took {duration:.3f}s, expected < 2.0s"
        assert len(runner.list_servers()) == 1000

    def test_server_lookup_performance(self):
        """Test performance of server lookups."""
        runner = E2BMCPRunner(api_key="test_key")
        
        # Add many servers
        num_servers = 1000
        for i in range(num_servers):
            config = ServerConfig(
                name=f"server_{i:04d}",
                command=f"python server_{i}.py"
            )
            runner.add_server(config)
        
        # Test lookup performance
        start_time = time.time()
        
        # Perform many lookups
        for i in range(1000):
            server_name = f"server_{i % num_servers:04d}"
            config = runner.get_server_config(server_name)
            assert config is not None
            
            info = runner.get_server_info(server_name)
            assert info is not None
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Lookups should be very fast (O(1) hash table lookups)
        assert duration < 0.1, f"1000 lookups took {duration:.3f}s, expected < 0.1s"

    def test_tool_validation_performance(self):
        """Test performance of tool parameter validation."""
        # Create a tool with many parameters
        properties = {}
        required = []
        
        for i in range(100):
            param_name = f"param_{i:03d}"
            properties[param_name] = {
                "type": "string",
                "description": f"Parameter {i}"
            }
            if i % 2 == 0:
                required.append(param_name)
        
        schema = {
            "type": "object",
            "properties": properties,
            "required": required
        }
        
        tool = Tool(
            name="complex_tool",
            description="Tool with many parameters",
            input_schema=schema
        )
        
        # Create valid parameters
        valid_params = {}
        for i in range(100):
            param_name = f"param_{i:03d}"
            valid_params[param_name] = f"value_{i}"
        
        # Test validation performance
        start_time = time.time()
        
        # Run validation many times
        for _ in range(1000):
            errors = tool.validate_parameters(valid_params)
            assert errors == []
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Validation should be reasonably fast
        assert duration < 1.0, f"1000 validations took {duration:.3f}s, expected < 1.0s"

    def test_parameter_extraction_performance(self):
        """Test performance of parameter extraction methods."""
        # Create a tool with many parameters
        properties = {}
        required = []
        
        for i in range(500):
            param_name = f"param_{i:03d}"
            properties[param_name] = {
                "type": "string",
                "description": f"Parameter {i}"
            }
            if i % 3 == 0:
                required.append(param_name)
        
        schema = {
            "type": "object",
            "properties": properties,
            "required": required
        }
        
        tool = Tool(name="large_tool", description="Tool with many parameters", input_schema=schema)
        
        # Test extraction performance
        start_time = time.time()
        
        for _ in range(1000):
            required_params = tool.get_required_parameters()
            optional_params = tool.get_optional_parameters()
            
            # Verify correctness
            assert len(required_params) > 0
            assert len(optional_params) > 0
            assert len(required_params) + len(optional_params) == 500
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Parameter extraction should be fast
        assert duration < 0.5, f"1000 extractions took {duration:.3f}s, expected < 0.5s"

    def test_memory_usage_with_large_configurations(self):
        """Test memory usage doesn't grow excessively with large configurations."""
        import sys
        
        runner = E2BMCPRunner(api_key="test_key")
        
        # Measure initial memory (rough approximation)
        initial_size = sys.getsizeof(runner.__dict__)
        
        # Add many large configurations
        for i in range(1000):
            config = ServerConfig(
                name=f"large_server_{i:04d}",
                command="python " + "very_long_command_" * 20 + f"server_{i}.py",
                description="Very long description: " + "Lorem ipsum " * 50,
                package="very-long-package-name-with-many-parts",
                env={
                    f"VAR_{j}": f"Very long environment variable value {j} " * 10
                    for j in range(10)
                }
            )
            runner.add_server(config)
        
        # Measure final memory
        final_size = sys.getsizeof(runner.__dict__)
        
        # Memory growth should be reasonable (not more than 100x initial size)
        memory_ratio = final_size / initial_size if initial_size > 0 else final_size
        assert memory_ratio < 100, f"Memory grew by {memory_ratio}x, which seems excessive"

    def test_concurrent_access_simulation(self):
        """Test concurrent access to runner methods."""
        runner = E2BMCPRunner(api_key="test_key")
        
        # Add some initial servers
        for i in range(100):
            config = ServerConfig(
                name=f"concurrent_server_{i:03d}",
                command=f"python server_{i}.py"
            )
            runner.add_server(config)
        
        def worker_function(worker_id):
            """Simulate concurrent worker accessing runner."""
            results = []
            
            # Each worker performs various operations
            for i in range(50):
                # List servers
                servers = runner.list_servers()
                results.append(len(servers))
                
                # Get server info
                server_name = f"concurrent_server_{(worker_id * 50 + i) % 100:03d}"
                info = runner.get_server_info(server_name)
                results.append(info is not None)
                
                # Get server config
                config = runner.get_server_config(server_name)
                results.append(config is not None)
            
            return results
        
        # Run concurrent workers
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker_function, i) for i in range(10)]
            results = [future.result() for future in futures]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Concurrent access should not take too long
        assert duration < 5.0, f"Concurrent access took {duration:.3f}s, expected < 5.0s"
        
        # All workers should have succeeded
        assert len(results) == 10
        for worker_results in results:
            assert len(worker_results) == 150  # 50 operations * 3 results each
            assert all(isinstance(result, (bool, int)) for result in worker_results)


class TestStressTesting:
    """Stress tests to verify library behavior under extreme conditions."""

    def test_maximum_server_configurations(self):
        """Test with very large number of server configurations."""
        runner = E2BMCPRunner(api_key="test_key")
        
        # Add a very large number of servers
        num_servers = 10000
        
        start_time = time.time()
        
        for i in range(num_servers):
            config = ServerConfig(
                name=f"stress_server_{i:05d}",
                command=f"python stress_server_{i}.py",
                description=f"Stress test server number {i}"
            )
            runner.add_server(config)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should handle large numbers of servers
        assert len(runner.list_servers()) == num_servers
        print(f"Added {num_servers} servers in {duration:.3f}s")
        
        # Test that operations still work with many servers
        test_server = f"stress_server_{num_servers // 2:05d}"
        config = runner.get_server_config(test_server)
        assert config is not None
        assert config.name == test_server

    def test_extremely_large_tool_schemas(self):
        """Test with extremely large tool schemas."""
        # Create an extremely large schema
        properties = {}
        required = []
        
        # 5000 parameters!
        for i in range(5000):
            param_name = f"param_{i:04d}"
            properties[param_name] = {
                "type": "string",
                "description": f"Parameter {i} with a very long description that goes on and on",
                "pattern": f"^[a-zA-Z0-9_-]{{1,{10 + i % 90}}}$",
                "examples": [f"example_{j}" for j in range(i % 5 + 1)]
            }
            if i % 4 == 0:
                required.append(param_name)
        
        schema = {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False
        }
        
        start_time = time.time()
        
        tool = Tool(
            name="extreme_tool",
            description="Tool with extremely large schema",
            input_schema=schema
        )
        
        # Test parameter extraction
        required_params = tool.get_required_parameters()
        optional_params = tool.get_optional_parameters()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should handle large schemas
        assert len(required_params) == 1250  # 5000 / 4
        assert len(optional_params) == 3750  # 5000 - 1250
        print(f"Processed schema with 5000 parameters in {duration:.3f}s")

    def test_rapid_configuration_changes(self):
        """Test rapid addition and lookup of configurations."""
        runner = E2BMCPRunner(api_key="test_key")
        
        start_time = time.time()
        
        # Rapidly add and access configurations
        for batch in range(10):
            # Add a batch of servers
            batch_configs = {}
            for i in range(100):
                server_name = f"batch_{batch:02d}_server_{i:03d}"
                batch_configs[server_name] = {
                    "command": f"python batch_{batch}_server_{i}.py",
                    "description": f"Batch {batch} server {i}"
                }
            
            runner.add_servers(batch_configs)
            
            # Immediately access some of them
            for i in range(0, 100, 10):  # Every 10th server
                server_name = f"batch_{batch:02d}_server_{i:03d}"
                config = runner.get_server_config(server_name)
                assert config is not None
                
                info = runner.get_server_info(server_name)
                assert info is not None
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should handle rapid changes efficiently
        assert len(runner.list_servers()) == 1000  # 10 batches * 100 servers
        print(f"Rapid configuration changes completed in {duration:.3f}s")

    def test_complex_validation_stress(self):
        """Stress test parameter validation with complex scenarios."""
        # Create a tool with complex validation requirements
        schema = {
            "type": "object",
            "properties": {
                "strings": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 1000
                },
                "nested": {
                    "type": "object",
                    "properties": {
                        "level1": {
                            "type": "object",
                            "properties": {
                                "level2": {"type": "array", "items": {"type": "integer"}}
                            }
                        }
                    }
                },
                "numbers": {
                    "type": "array",
                    "items": {"type": "number"}
                }
            },
            "required": ["strings", "nested"]
        }
        
        tool = Tool(name="stress_tool", description="Stress test tool", input_schema=schema)
        
        # Create complex test parameters
        test_params = {
            "strings": [f"string_{i}" for i in range(500)],
            "nested": {
                "level1": {
                    "level2": list(range(100))
                }
            },
            "numbers": [float(i) for i in range(200)]
        }
        
        start_time = time.time()
        
        # Run validation many times
        for _ in range(1000):
            errors = tool.validate_parameters(test_params)
            assert errors == []
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"1000 complex validations completed in {duration:.3f}s")
        
        # Should handle complex validation efficiently
        assert duration < 5.0, f"Complex validation took {duration:.3f}s, expected < 5.0s"

    def test_memory_pressure_simulation(self):
        """Simulate memory pressure with many large objects."""
        runner = E2BMCPRunner(api_key="test_key")
        
        # Create many configurations with large data
        large_data = "x" * 10000  # 10KB string
        
        for i in range(1000):
            config = ServerConfig(
                name=f"memory_test_{i:04d}",
                command=f"python {large_data[:100]}_server_{i}.py",  # Truncated for command
                description=large_data,  # Full large string in description
                env={
                    f"LARGE_VAR_{j}": large_data for j in range(5)  # 5 * 10KB per server
                }
            )
            runner.add_server(config)
        
        # Test that operations still work under memory pressure
        start_time = time.time()
        
        # Perform many operations
        for i in range(1000):
            server_name = f"memory_test_{i:04d}"
            
            # These operations should not be significantly slower due to memory pressure
            config = runner.get_server_config(server_name)
            assert config is not None
            assert len(config.description) == 10000
            
            info = runner.get_server_info(server_name)
            assert info is not None
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Operations under memory pressure completed in {duration:.3f}s")
        
        # Operations should still be reasonably fast even with large data
        assert duration < 2.0, f"Operations under memory pressure took {duration:.3f}s"


class TestScalability:
    """Test scalability characteristics."""

    def test_linear_scaling_server_addition(self):
        """Test that server addition scales linearly."""
        runner = E2BMCPRunner(api_key="test_key")
        
        # Test different batch sizes
        batch_sizes = [100, 500, 1000, 2000]
        times = []
        
        for batch_size in batch_sizes:
            # Clear previous servers
            runner = E2BMCPRunner(api_key="test_key")
            
            start_time = time.time()
            
            for i in range(batch_size):
                config = ServerConfig(
                    name=f"scale_server_{i:05d}",
                    command=f"python server_{i}.py"
                )
                runner.add_server(config)
            
            end_time = time.time()
            duration = end_time - start_time
            times.append(duration)
            
            print(f"Added {batch_size} servers in {duration:.3f}s ({batch_size/duration:.1f} servers/sec)")
        
        # Check that scaling is reasonable (not exponential)
        # Time per server should not increase dramatically
        time_per_server = [times[i] / batch_sizes[i] for i in range(len(batch_sizes))]
        
        # Later batches shouldn't be more than 3x slower per server than first batch
        for i in range(1, len(time_per_server)):
            ratio = time_per_server[i] / time_per_server[0]
            assert ratio < 3.0, f"Time per server increased by {ratio:.2f}x, indicating poor scaling"

    def test_lookup_performance_scaling(self):
        """Test that lookup performance doesn't degrade with more servers."""
        runner = E2BMCPRunner(api_key="test_key")
        
        # Test lookup performance at different scales
        scales = [100, 500, 1000, 5000]
        lookup_times = []
        
        for scale in scales:
            # Add servers up to this scale
            while len(runner.list_servers()) < scale:
                current_count = len(runner.list_servers())
                config = ServerConfig(
                    name=f"lookup_server_{current_count:05d}",
                    command=f"python server_{current_count}.py"
                )
                runner.add_server(config)
            
            # Time lookups
            start_time = time.time()
            
            # Perform random lookups
            import random
            for _ in range(1000):
                server_idx = random.randint(0, scale - 1)
                server_name = f"lookup_server_{server_idx:05d}"
                config = runner.get_server_config(server_name)
                assert config is not None
            
            end_time = time.time()
            duration = end_time - start_time
            lookup_times.append(duration)
            
            print(f"1000 lookups with {scale} servers took {duration:.3f}s")
        
        # Lookup time should not increase significantly (hash table should be O(1))
        # Allow some variation but not exponential growth
        for i in range(1, len(lookup_times)):
            ratio = lookup_times[i] / lookup_times[0]
            assert ratio < 2.0, f"Lookup time increased by {ratio:.2f}x at scale {scales[i]}" 