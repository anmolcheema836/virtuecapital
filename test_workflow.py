import time
import re
from playwright.sync_api import sync_playwright, expect

# Configuration
FRONTEND_URL = "http://localhost:5173"
PORT = FRONTEND_URL.split(":")[-1] if ":" in FRONTEND_URL.replace("http://", "") else "80"

RUN_ID = str(int(time.time()))[-6:]

TENANT = {
    "cafeName": f"Test Cafe {RUN_ID}",
    "subdomain": f"testcafe{RUN_ID}",
    "ownerName": "Admin Tester",
    "email": f"admin{RUN_ID}@nexapot.com",
    "phone": f"99999{RUN_ID}",
    "password": "SecurePassword123!"
}

TENANT_URL = f"http://{TENANT['subdomain']}.localhost:{PORT}"

CUSTOMER = {
    "name": "John Customer",
    "phone": f"88888{RUN_ID}",
    "password": "CustomerPass123!"
}

def run(playwright):
    browser = playwright.chromium.launch(headless=False)
    
    # Context 1: Admin Desktop
    admin_context = browser.new_context()
    admin_page = admin_context.new_page()
    
    # Context 2: Customer Mobile (iPhone 12 Pro Viewport)
    customer_context = browser.new_context(
        viewport={'width': 390, 'height': 844},
        user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1'
    )
    customer_page = customer_context.new_page()

    print(f"\n--- Starting Nexapot E2E UI Test [{RUN_ID}] ---")

    try:
        # ---------------------------------------------------------
        print("1. SaaS Onboarding - Registering Cafe...")
        # ---------------------------------------------------------
        
        def intercept_payment_redirect(route):
            response = route.fetch()
            try:
                data = response.json()
                if data.get("success") and "data" in data and "payment_url" in data["data"]:
                    data["data"]["payment_url"] = None 
                route.fulfill(status=response.status, headers=response.headers, json=data)
            except:
                route.fulfill(response=response)

        admin_page.route("**/api/onboarding/register", intercept_payment_redirect)

        admin_page.goto(f"{FRONTEND_URL}/register")
        
        admin_page.get_by_placeholder("e.g. The Daily Grind").fill(TENANT["cafeName"])
        admin_page.get_by_placeholder("dailygrind").fill(TENANT["subdomain"])
        admin_page.get_by_role("button", name=re.compile("Continue to Admin Setup", re.IGNORECASE)).click()

        admin_page.get_by_placeholder("John Doe").fill(TENANT["ownerName"])
        admin_page.get_by_placeholder("john@example.com").fill(TENANT["email"])
        admin_page.get_by_placeholder("••••••••").fill(TENANT["password"])
        admin_page.get_by_text("India (INR)").click()
        admin_page.get_by_role("button", name=re.compile("Start Trial & Subscribe", re.IGNORECASE)).click()

        expect(admin_page.get_by_text("Cafe Ready!")).to_be_visible(timeout=15000)
        admin_page.unroute("**/api/onboarding/register")

        admin_page.wait_for_timeout(1000) 

        # ---------------------------------------------------------
        print(f"2. Admin Login & Menu Setup (via {TENANT_URL})...")
        # ---------------------------------------------------------
        admin_page.goto(f"{TENANT_URL}/admin/login")
        
        admin_page.get_by_placeholder("staff@cafe.com").fill(TENANT["email"])
        admin_page.get_by_placeholder("••••••••").fill(TENANT["password"])
        admin_page.get_by_role("button", name="Sign In").click()

        expect(admin_page.get_by_role("heading", name="New Order")).to_be_visible(timeout=10000)

        # FIX: Route directly to Categories to prevent accordion toggle flakiness
        admin_page.goto(f"{TENANT_URL}/admin/categories")

        # Setup Category
        admin_page.get_by_placeholder("e.g. Hot Coffees").fill("Hot Beverages")
        admin_page.get_by_role("button", name="Create Category").click()
        expect(admin_page.get_by_text("Hot Beverages")).to_be_visible()

        # FIX: Route directly to Menu Master
        admin_page.goto(f"{TENANT_URL}/admin/menu")

        # Setup Item
        admin_page.locator('select[name="category_id"]').select_option(label="Hot Beverages")
        admin_page.get_by_placeholder("e.g. Latte").fill("Caramel Macchiato")
        admin_page.locator('input[name="base_price"]').fill("250")
        admin_page.locator('textarea[name="short_description"]').fill("Delicious automated coffee test.")
        
        admin_page.get_by_role("button", name="Save to Menu").click()
        expect(admin_page.get_by_text("Caramel Macchiato")).to_be_visible()

        admin_page.wait_for_timeout(1000) 

        # ---------------------------------------------------------
        print("3. Customer App - Registration & Checkout...")
        # ---------------------------------------------------------
        customer_page.goto(f"{TENANT_URL}/auth")
        
        customer_page.get_by_role("button", name="Create Account").first.click()
        
        customer_page.locator('input[type="text"]').fill(CUSTOMER["name"])
        customer_page.get_by_placeholder("9876543210").fill(CUSTOMER["phone"])
        customer_page.get_by_placeholder("••••••••").fill(CUSTOMER["password"])
        
        customer_page.locator('button[type="submit"]').click()

        expect(customer_page.get_by_text("Welcome back!")).to_be_visible(timeout=10000)

        # Order item
        customer_page.goto(f"{TENANT_URL}/menu")
        customer_page.get_by_text("Caramel Macchiato").click()
        customer_page.get_by_placeholder("e.g. Less ice, extra spicy...").fill("Make it extra hot please.")
        customer_page.get_by_role("button", name=re.compile("Add to Cart", re.IGNORECASE)).click()

        # Checkout
        customer_page.get_by_text("View Cart").click(force=True)
        customer_page.get_by_role("button", name=re.compile("Proceed to Checkout", re.IGNORECASE)).click()
        customer_page.get_by_text("Pay at Counter").click()
        customer_page.get_by_role("button", name=re.compile("Confirm Order & Checkout", re.IGNORECASE)).click()

        expect(customer_page.get_by_text("Tracking your order in real-time")).to_be_visible(timeout=10000)
        expect(customer_page.get_by_text("Order Placed")).to_be_visible()

        # ---------------------------------------------------------
        print("4. Kitchen KDS - Order Fulfillment...")
        # ---------------------------------------------------------
        # FIX: Route directly to Kitchen KDS
        admin_page.goto(f"{TENANT_URL}/admin/kitchen")

        expect(admin_page.get_by_text("Caramel Macchiato")).to_be_visible()
        expect(admin_page.get_by_text("Make it extra hot please.")).to_be_visible()

        # Cash orders skip 'Accept' and go straight to Preparing
        expect(admin_page.get_by_role("button", name="Start Preparing")).to_be_visible()
        admin_page.get_by_role("button", name="Start Preparing").click()
        
        expect(admin_page.get_by_role("button", name="Mark Ready")).to_be_visible()
        admin_page.get_by_role("button", name="Mark Ready").click()
        
        expect(admin_page.get_by_role("button", name="Dispatch / Serve")).to_be_visible()
        admin_page.get_by_role("button", name="Dispatch / Serve").click()

        # ---------------------------------------------------------
        print("5. POS - Settle Payment...")
        # ---------------------------------------------------------
        # FIX: Route directly to Active Orders to bypass sidebar toggle logic
        admin_page.goto(f"{TENANT_URL}/admin/orders")
        
        admin_page.get_by_role("button", name="Settle Bill").click()

        expect(admin_page.get_by_text("Process Payment")).to_be_visible()
        admin_page.get_by_text("Cash").click()
        admin_page.get_by_role("button", name=re.compile("Mark as Paid", re.IGNORECASE)).click()

        expect(admin_page.get_by_text("Order is Settled")).to_be_visible()

        # ---------------------------------------------------------
        print("6. Verify Customer Status...")
        # ---------------------------------------------------------
        expect(customer_page.get_by_text("Order Completed!")).to_be_visible(timeout=10000)
        customer_page.goto(f"{TENANT_URL}/profile")
        
        # Base price 250 * 10% = 25 points
        expect(customer_page.get_by_text("25", exact=True)).to_be_visible()

        print("\n✅ All UI Workflows Verified Successfully!")

    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
    finally:
        admin_context.close()
        customer_context.close()
        browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)