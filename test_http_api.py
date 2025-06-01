#!/usr/bin/env python3
"""
HTTP API testing script for AI Command Gateway.
Tests the service via real HTTP calls with comprehensive scenarios.
"""

import requests
import json
import time
from uuid import uuid4
from datetime import datetime, timezone
import sys
from typing import Dict, Any


class GatewayAPITester:
    """Comprehensive HTTP API tester for AI Command Gateway."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "AI-Command-Gateway-Tester/1.0"
        })
        
    def test_health_check(self) -> bool:
        """Test the health check endpoint."""
        print("🔍 Testing health check endpoint...")
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check successful")
                print(f"   Status: {data.get('status')}")
                print(f"   Gateway ID: {data.get('gateway_id')}")
                print(f"   Execution Strategy: {data.get('checks', {}).get('execution_strategy')}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def create_test_request(self, logical_name: str = "market-predictor", intent: str = "restart the service") -> Dict[str, Any]:
        """Create a test request."""
        return {
            "request_id": str(uuid4()),
            "source_agent_id": "http-test-client",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "target_resource": {
                "logical_name": logical_name
            },
            "action_request": {
                "intent_or_command_description": intent
            }
        }
    
    def test_basic_command_execution(self) -> bool:
        """Test basic command execution."""
        print("\\n🔍 Testing basic command execution...")
        
        request_data = self.create_test_request(
            logical_name="market-predictor",
            intent="restart the service due to performance issues"
        )
        
        try:
            response = self.session.post(
                f"{self.base_url}/execute-docker-command",
                json=request_data
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Command execution successful")
                print(f"   Overall Status: {data.get('overall_status')}")
                print(f"   Summary: {data.get('summary_message_from_gateway')}")
                
                if 'execution_details' in data:
                    details = data['execution_details']
                    print(f"   Generated Command: {details.get('docker_command_generated_by_llm')}")
                    if 'execution_result' in details:
                        result = details['execution_result']
                        print(f"   Execution Status: {result.get('status')}")
                        print(f"   Exit Code: {result.get('exit_code')}")
                
                return data.get('overall_status') in ['COMPLETED_SUCCESS', 'COMPLETED_FAILURE']
            else:
                print(f"❌ Command execution failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Command execution error: {e}")
            return False
    
    def test_all_services(self) -> bool:
        """Test command execution for all supported services."""
        print("\\n🔍 Testing all supported services...")
        
        services = ["market-predictor", "coding-ai-agent", "devops-ai-agent"]
        results = []
        
        for service in services:
            print(f"   Testing {service}...")
            
            request_data = self.create_test_request(
                logical_name=service,
                intent="check container status"
            )
            
            try:
                response = self.session.post(
                    f"{self.base_url}/execute-docker-command",
                    json=request_data
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('overall_status')
                    print(f"      ✅ {service}: {status}")
                    results.append(True)
                else:
                    print(f"      ❌ {service}: HTTP {response.status_code}")
                    results.append(False)
                    
            except Exception as e:
                print(f"      ❌ {service}: {e}")
                results.append(False)
        
        success_rate = sum(results) / len(results) * 100
        print(f"   Success rate: {success_rate:.1f}% ({sum(results)}/{len(results)})")
        
        return all(results)
    
    def test_complex_intents(self) -> bool:
        """Test various complex intent scenarios."""
        print("\\n🔍 Testing complex intent scenarios...")
        
        test_cases = [
            {
                "intent": "restart the service because it's using too much memory",
                "description": "Memory issue restart"
            },
            {
                "intent": "get the last 50 lines of logs to investigate errors",
                "description": "Log investigation"
            },
            {
                "intent": "check if the container is running and healthy",
                "description": "Health check"
            },
            {
                "intent": "show container resource usage statistics",
                "description": "Resource monitoring"
            }
        ]
        
        results = []
        
        for case in test_cases:
            print(f"   Testing: {case['description']}...")
            
            request_data = self.create_test_request(
                logical_name="market-predictor",
                intent=case['intent']
            )
            
            try:
                response = self.session.post(
                    f"{self.base_url}/execute-docker-command",
                    json=request_data
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('overall_status')
                    
                    if 'execution_details' in data:
                        command = data['execution_details'].get('docker_command_generated_by_llm', 'N/A')
                        print(f"      ✅ {case['description']}: {status}")
                        print(f"         Generated: {command}")
                        results.append(True)
                    else:
                        print(f"      ⚠️ {case['description']}: No execution details")
                        results.append(False)
                else:
                    print(f"      ❌ {case['description']}: HTTP {response.status_code}")
                    results.append(False)
                    
            except Exception as e:
                print(f"      ❌ {case['description']}: {e}")
                results.append(False)
        
        success_rate = sum(results) / len(results) * 100
        print(f"   Success rate: {success_rate:.1f}% ({sum(results)}/{len(results)})")
        
        return sum(results) >= len(results) * 0.8  # 80% success rate
    
    def test_error_scenarios(self) -> bool:
        """Test error handling scenarios."""
        print("\\n🔍 Testing error scenarios...")
        
        # Test unknown service
        print("   Testing unknown service...")
        request_data = self.create_test_request(
            logical_name="unknown-service",
            intent="restart the service"
        )
        
        try:
            response = self.session.post(
                f"{self.base_url}/execute-docker-command",
                json=request_data
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('overall_status') == 'VALIDATION_ERROR':
                    print("      ✅ Unknown service properly rejected")
                    unknown_service_ok = True
                else:
                    print(f"      ❌ Unexpected status: {data.get('overall_status')}")
                    unknown_service_ok = False
            else:
                print(f"      ❌ Unexpected HTTP status: {response.status_code}")
                unknown_service_ok = False
                
        except Exception as e:
            print(f"      ❌ Unknown service test error: {e}")
            unknown_service_ok = False
        
        # Test malformed request
        print("   Testing malformed request...")
        malformed_request = {"invalid": "request"}
        
        try:
            response = self.session.post(
                f"{self.base_url}/execute-docker-command",
                json=malformed_request
            )
            
            if response.status_code == 422:  # Validation error
                print("      ✅ Malformed request properly rejected")
                malformed_ok = True
            else:
                print(f"      ❌ Unexpected status code: {response.status_code}")
                malformed_ok = False
                
        except Exception as e:
            print(f"      ❌ Malformed request test error: {e}")
            malformed_ok = False
        
        return unknown_service_ok and malformed_ok
    
    def test_incident_context(self) -> bool:
        """Test requests with incident context."""
        print("\\n🔍 Testing incident context support...")
        
        request_data = self.create_test_request(
            logical_name="market-predictor",
            intent="restart the service to resolve performance issues"
        )
        
        # Add incident context
        request_data["incident_context"] = {
            "summary": "High memory usage and slow response times detected",
            "key_data_points": [
                {"type": "metric", "name": "memory_usage", "value": "85%"},
                {"type": "metric", "name": "avg_response_time", "value": "2.5s"},
                {"type": "metric", "name": "error_rate", "value": "12%"}
            ]
        }
        
        request_data["action_request"]["expected_outcome_description"] = "Service should return to normal performance levels"
        
        try:
            response = self.session.post(
                f"{self.base_url}/execute-docker-command",
                json=request_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Incident context request successful")
                print(f"      Status: {data.get('overall_status')}")
                print(f"      Summary: {data.get('summary_message_from_gateway')}")
                return True
            else:
                print(f"   ❌ Incident context request failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Incident context test error: {e}")
            return False
    
    def run_comprehensive_tests(self) -> Dict[str, bool]:
        """Run all tests and return results."""
        print("🚀 AI Command Gateway - HTTP API Comprehensive Testing")
        print("=" * 70)
        
        tests = {
            "health_check": self.test_health_check,
            "basic_command": self.test_basic_command_execution,
            "all_services": self.test_all_services,
            "complex_intents": self.test_complex_intents,
            "error_scenarios": self.test_error_scenarios,
            "incident_context": self.test_incident_context
        }
        
        results = {}
        
        for test_name, test_func in tests.items():
            try:
                result = test_func()
                results[test_name] = result
                time.sleep(0.5)  # Brief pause between tests
            except Exception as e:
                print(f"❌ Test {test_name} failed with exception: {e}")
                results[test_name] = False
        
        print("\\n" + "=" * 70)
        print("📊 Test Results Summary:")
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name:20} {status}")
            if result:
                passed += 1
        
        print(f"\\n🎯 Overall Result: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED - Service is robust and ready!")
        elif passed >= total * 0.8:
            print("✅ Most tests passed - Service is functional with minor issues")
        else:
            print("⚠️ Multiple test failures - Service needs attention")
        
        return results


def main():
    """Main test execution."""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8080"
    
    print(f"Testing AI Command Gateway at: {base_url}")
    
    tester = GatewayAPITester(base_url)
    results = tester.run_comprehensive_tests()
    
    # Exit with appropriate code
    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()