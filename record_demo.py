import asyncio
import os
import shutil
from playwright.async_api import async_playwright

OUTPUT_DIR = "/config/Desktop/Session1/demo_output"

async def record_demo():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = await browser.new_context(
            record_video_dir=OUTPUT_DIR,
            record_video_size={"width": 1280, "height": 720},
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        
        print("1. Navigating to http://localhost:8080...")
        await page.goto("http://localhost:8080")
        await page.wait_for_timeout(2000)
        
        # Prompt 1: Showcasing core app feature (pantry lookup & recipe suggestion)
        prompt1 = "What ingredients do I have in my pantry and what recipes can I make?"
        print(f"2. Sending Prompt 1: {prompt1}")
        
        await page.fill("#input", prompt1)
        await page.wait_for_timeout(1000)
        await page.click("button[type='submit']")
        
        # Wait for agent response
        print("3. Waiting for response to Prompt 1...")
        await page.wait_for_selector(".msg-wrapper.agent:not(#typingIndicatorMsg)", timeout=30000)
        await page.wait_for_timeout(6000)  # pause to let viewer read response
        
        # Prompt 2: Richer prompt showing tool call, Firestore lookup & video generation
        prompt2 = "Find my Margherita Pizza recipe in Firestore and generate a short video for it!"
        print(f"4. Sending Prompt 2: {prompt2}")
        
        await page.fill("#input", prompt2)
        await page.wait_for_timeout(1000)
        await page.click("button[type='submit']")
        
        # Wait for second agent response (video generation takes ~35-45s)
        print("5. Waiting for response to Prompt 2 (video tool call)...")
        # Wait for typing indicator to disappear
        for _ in range(60):
            await page.wait_for_timeout(1000)
            agents = await page.query_selector_all(".msg-wrapper.agent:not(#typingIndicatorMsg)")
            if len(agents) >= 2:
                print("Second agent response received!")
                break
                
        # Final pause to showcase result
        await page.wait_for_timeout(8000)
        
        video_path = await page.video.path()
        print(f"Raw Playwright video saved to: {video_path}")
        
        await context.close()
        await browser.close()
        
        target_path = "/config/Desktop/Session1/demo_video.webm"
        shutil.copy(video_path, target_path)
        print(f"SUCCESS! Copied final demo video to: {target_path}")

if __name__ == "__main__":
    asyncio.run(record_demo())
