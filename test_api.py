import requests
import json

# API base URL
BASE_URL = "http://localhost:5000/api"

def test_health():
    """Test the health check endpoint"""
    print("\n--- Testing Health Check Endpoint ---")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_model_info():
    """Test the model info endpoint"""
    print("\n--- Testing Model Info Endpoint ---")
    response = requests.get(f"{BASE_URL}/model-info")
    print(f"Status code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_extract_arguments():
    """Test the extract arguments endpoint"""
    print("\n--- Testing Extract Arguments Endpoint ---")
    
    # Sample legal texts
    moving_text = """
DEFENDANT'S MOTION TO DISMISS SHOULD BE DENIED.

Plaintiffs own properties located in Franklin County, Virginia in the area around Boones Mill. MVP holds an easement to construct and maintain a natural gas pipeline across each of the properties.

THIS COURT HAS JURISDICTION TO HEAR PLAINTIFFS' CLAIMS UNDER THE CITIZEN SUIT PROVISION OF THE CLEAN WATER ACT.

Plaintiffs bring this action under the citizen suit provision of the Clean Water Act, 33 U.S.C. § 1365(a). The Clean Water Act ("CWA") prohibits the discharge of pollutants, including dredged or fill material, into waters of the United States.
"""

    response_text = """
THE COURT SHOULD DISMISS THIS ACTION FOR LACK OF SUBJECT MATTER JURISDICTION.

Plaintiffs impermissibly attempt to premise subject matter jurisdiction on a claim that Defendant Mountain Valley Pipeline, LLC ("MVP") has violated the conditions of a permit issued by the Commonwealth of Virginia.

THE PLAINTIFFS' CLAIMS ARE BARRED BY ELEVENTH AMENDMENT SOVEREIGN IMMUNITY.

The Eleventh Amendment bars federal courts from hearing claims that a state or state official has violated state law. Pennhurst State Sch. & Hosp. v. Halderman, 465 U.S. 89, 106 (1984).

THE CLEAN WATER ACT DOES NOT PROVIDE A BASIS FOR CITIZEN SUIT ENFORCEMENT OF STATE-ISSUED PERMITS.

Plaintiffs' attempt to bring a "citizen suit" to enforce the conditions of a state-issued permit fails because the Clean Water Act does not authorize such claims.
"""

    payload = {
        "moving_text": moving_text,
        "response_text": response_text
    }
    
    response = requests.post(f"{BASE_URL}/extract-arguments", json=payload)
    print(f"Status code: {response.status_code}")
    print(f"Response preview: {json.dumps(response.json(), indent=2)[:500]}...")
    
    # Save the extracted arguments for the next test
    if response.status_code == 200:
        extracted_args = response.json()
        print(f"Extracted {len(extracted_args['moving_brief']['brief_arguments'])} moving arguments")
        print(f"Extracted {len(extracted_args['response_brief']['brief_arguments'])} response arguments")
        return True, extracted_args
    else:
        return False, None

def test_link_arguments(extracted_args):
    """Test the link arguments endpoint"""
    print("\n--- Testing Link Arguments Endpoint ---")
    
    if not extracted_args:
        print("No extracted arguments to test with.")
        return False
    
    payload = {
        "moving_brief": extracted_args["moving_brief"],
        "response_brief": extracted_args["response_brief"],
        "threshold": 0.3,
        "max_links_per_arg": 2
    }
    
    response = requests.post(f"{BASE_URL}/link-arguments", json=payload)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Found {len(result['links'])} links between arguments")
        print("Links:")
        for link in result['links']:
            print(f"- Moving: '{link['moving_heading'][:30]}...' -> Response: '{link['response_heading'][:30]}...' (Confidence: {link['confidence']:.2f})")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def run_all_tests():
    """Run all API tests"""
    print("=== Starting API Tests ===")
    
    # Test health endpoint
    health_ok = test_health()
    
    # Test model info endpoint
    model_info_ok = test_model_info()
    
    # Test extract arguments endpoint
    extract_ok, extracted_args = test_extract_arguments()
    
    # Test link arguments endpoint (only if extract succeeded)
    if extract_ok:
        link_ok = test_link_arguments(extracted_args)
    else:
        link_ok = False
        print("Skipping link arguments test due to extract arguments failure.")
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Health Check: {'✓' if health_ok else '✗'}")
    print(f"Model Info: {'✓' if model_info_ok else '✗'}")
    print(f"Extract Arguments: {'✓' if extract_ok else '✗'}")
    print(f"Link Arguments: {'✓' if link_ok else '✗'}")
    
    if health_ok and model_info_ok and extract_ok and link_ok:
        print("\n🎉 All tests passed! The API is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the API logs for errors.")

if __name__ == "__main__":
    run_all_tests()