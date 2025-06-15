import asyncio
from playwright.async_api import async_playwright
import nest_asyncio
import re
from datetime import datetime, timedelta
import json

# Allow nested event loops (useful in Jupyter)
nest_asyncio.apply()

class DetailsScraping:
    def __init__(self, url, retries=3):
        self.url = url
        self.retries = retries  # Retry count for robustness

    # async def get_property_details(self):
    #     async with async_playwright() as p:
    #         browser = await p.chromium.launch(headless=True)
    #         page = await browser.new_page()

    #         # Set timeouts
    #         page.set_default_navigation_timeout(300000)
    #         page.set_default_timeout(300000)  # General timeout

    #         properties = []  # To store scraped properties

    #         for attempt in range(self.retries):
    #             try:
    #                 # Navigate to the page
    #                 await page.goto(self.url, wait_until="domcontentloaded")
    #                 await page.wait_for_selector('.StackedCard_card__Kvggc', timeout=300000)

    #                 # Extract property details
    #                 property_cards = await page.query_selector_all('.StackedCard_card__Kvggc')
    #                 for card in property_cards:
    #                     # Extract property information
    #                     link = await self.scrape_link(card)
    #                     property_type = await self.scrape_property_type(card)
    #                     title = await self.scrape_title(card)
    #                     description = await self.scrape_description(card)
    #                     pinned_today = await self.scrape_pinned_today(card)
    #                     id = await self.scrape_id(link)

    #                     # Scrape additional details from the property page
    #                     additional_details = await self.scrape_additional_details(link)

    #                     properties.append({
    #                         'id': id,
    #                         'date_published': additional_details.get('date_published'),
    #                         'relative_date': additional_details.get('relative_date'),
    #                         'pin': pinned_today,
    #                         'type': property_type,
    #                         'title': title,
    #                         'description': description,
    #                         'link': link,
    #                         'image': additional_details.get('image'),
    #                         'price': additional_details.get('price'),
    #                         'address': additional_details.get('address'),
    #                         'beds': additional_details.get('beds'),
    #                         'area': additional_details.get('area'),
    #                         'specifications': additional_details.get('specifications'),
    #                         'views_no': additional_details.get('views_no'),  # Added views number here
    #                         'submitter': additional_details.get('submitter'),
    #                         'ads': additional_details.get('ads'),
    #                         'membership': additional_details.get('membership'),
    #                         'phone': additional_details.get('phone'),
    #                     })
    #                 break  # Exit loop if successful

    #             except Exception as e:
    #                 print(f"Attempt {attempt + 1} failed for {self.url}: {e}")
    #                 if attempt + 1 == self.retries:
    #                     print(f"Max retries reached for {self.url}. Returning partial results.")
    #                     break
    #             finally:
    #                 # Close page between attempts to ensure proper cleanup
    #                 await page.close()
    #                 if attempt + 1 < self.retries:
    #                     page = await browser.new_page()

    #         await browser.close()
    #         return properties
    
    async def get_property_details(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            page.set_default_navigation_timeout(20000)
            page.set_default_timeout(20000)
    
            properties = []
            for attempt in range(self.retries):
                try:
                    print(f"[{self.url}] Attempt {attempt+1} - Navigating ...")
                    await page.goto(self.url, wait_until="domcontentloaded")
                    print(f"[{self.url}] Page loaded, waiting for selector ...")
                    await page.wait_for_selector('a.StackedCard_wrapper__acC1w', timeout=10000)
                    anchors = await page.query_selector_all('a.StackedCard_wrapper__acC1w')
                    print(f"[{self.url}] Found {len(anchors)} property anchors.")
    
                    for anchor in anchors:
                        rawlink = await anchor.get_attribute('href')
                        if not rawlink:
                            print(f"[{self.url}] Skipping anchor with no href.")
                            continue
                        base_url = 'https://www.q84sale.com'
                        link = f"{base_url}{rawlink}"
    
                        # Card info is inside the anchor
                        card = await anchor.query_selector('.StackedCard_card__Kvggc')
                        if not card:
                            print(f"[{self.url}] Anchor missing card div, skipping.")
                            continue
    
                        # Use your existing methods, passing `card` as before:
                        property_type = await self.scrape_property_type(card)
                        title = await self.scrape_title(card)
                        description = await self.scrape_description(card)
                        pinned_today = await self.scrape_pinned_today(card)
                        id = await self.scrape_id(link)
    
                        additional_details = await self.scrape_additional_details(link)
    
                        properties.append({
                            'id': id,
                            'date_published': additional_details.get('date_published'),
                            'relative_date': additional_details.get('relative_date'),
                            'pin': pinned_today,
                            'type': property_type,
                            'title': title,
                            'description': description,
                            'link': link,
                            'image': additional_details.get('image'),
                            'price': additional_details.get('price'),
                            'address': additional_details.get('address'),
                            'beds': additional_details.get('beds'),
                            'area': additional_details.get('area'),
                            'specifications': additional_details.get('specifications'),
                            'views_no': additional_details.get('views_no'),
                            'submitter': additional_details.get('submitter'),
                            'ads': additional_details.get('ads'),
                            'membership': additional_details.get('membership'),
                            'phone': additional_details.get('phone'),
                        })
                    break  # exit retry loop on success
                except Exception as e:
                    print(f"[{self.url}] Attempt {attempt + 1} failed: {e}")
                    if attempt + 1 == self.retries:
                        print(f"[{self.url}] Max retries reached. Returning partial results.")
                        break
                finally:
                    await page.close()
                    if attempt + 1 < self.retries:
                        page = await browser.new_page()
            await browser.close()
            return properties
    
    # Method to scrape the link
    async def scrape_link(self, card):
        rawlink = await card.get_attribute('href')
        base_url = 'https://www.q84sale.com'
        return f"{base_url}{rawlink}" if rawlink else None

    # Method to scrape the property type
    async def scrape_property_type(self, card):
        selector = '.text-6-med.text-neutral_600.styles_category__NQAci'
        element = await card.query_selector(selector)
        return await element.inner_text() if element else None

    # Method to scrape the property title
    async def scrape_title(self, card):
        selector = '.text-4-med.text-neutral_900.styles_title__l5TTA'
        element = await card.query_selector(selector)
        return await element.inner_text() if element else None

    # Method to scrape the property description
    async def scrape_description(self, card):
        selector = '.text-5-regular.text-neutral_500.StackedCard_description__aXpyG'
        element = await card.query_selector(selector)
        return await element.inner_text() if element else None

    # Method to scrape the pin status
    async def scrape_pinned_today(self, card):
        selector = '.styles_tail__82mnX p.text-6-med.text-neutral_600'
        elements = await card.query_selector_all(selector)
        if elements:
            pin_text = await elements[0].inner_text()
            return "Pinned today" if pin_text == "Pinned today" else "Not Pinned"
        return "Not Pinned"

    # New method to scrape the x value (second value)
    async def scrape_relative_date(self, page):
        try:
            # Define the parent container selector
            parent_selector = '.d-flex.styles_topData__Sx1GF'

            # Locate the parent container and get all the child divs with the desired class
            parent_locator = page.locator(parent_selector)

            # Wait for the parent container to be visible before proceeding
            await parent_locator.wait_for(state="visible", timeout=10000)

            # Get all child div elements with the class 'd-flex align-items-center styles_dataWithIcon__For9u'
            child_divs = parent_locator.locator('.d-flex.align-items-center.styles_dataWithIcon__For9u')

            # Wait until the elements are available and then fetch the second child div
            await child_divs.first.wait_for(state="visible", timeout=10000)  # Ensure first child is available
            await child_divs.nth(1).wait_for(state="visible", timeout=10000)  # Wait for second child to be visible

            # Extract the x value (content of the second div)
            relative_time_locator = child_divs.nth(1).locator('div.text-5-regular.m-text-6-med.text-neutral_600')
            relative_time_text = await relative_time_locator.inner_text()
            if relative_time_text:
                stripped_time = relative_time_text.replace(" ago", "").strip()
                return stripped_time  # Clean up whitespace
            else:
                print("relative_time value not found.")
                return None

        except Exception as e:
            print(f"Error while scraping relative_time value: {e}")
            return None

    # Method to scrape date_published
    async def scrape_publish_date(self, relative_time):
        # Regex to find relative time strings like "5 Hours ago" or "30 Minutes ago"
        relative_time_pattern = r'(\d+)\s+(Second|Minute|Hour|Day)'

        # Search for relative time in the input string
        match = re.search(relative_time_pattern, relative_time, re.IGNORECASE)
        if not match:
            return "Invalid Relative Time"

        # Extract the number and unit (Seconds, Minutes, or Hours)
        number = int(match.group(1))
        unit = match.group(2).lower()

        # Get the current date and time
        current_time = datetime.now()

        # Calculate the publish date
        if unit == "second":
            publish_time = current_time - timedelta(seconds=number)
        elif unit == "minute":
            publish_time = current_time - timedelta(minutes=number)
        elif unit == "hour":
            publish_time = current_time - timedelta(hours=number)
        elif unit == "day":
            publish_time = current_time - timedelta(days=number)
        else:
            return "Unsupported time unit found."

        return publish_time.strftime("%Y-%m-%d %H:%M:%S")

    # New method to scrape the number of views
    async def scrape_views_no(self, page):
        try:
            # Define the selector for the views number
            views_selector = '.d-flex.align-items-center.styles_dataWithIcon__For9u .text-5-regular.m-text-6-med.text-neutral_600'

            # Locate the element and extract its text
            views_element = await page.query_selector(views_selector)

            if views_element:
                views_no = await views_element.inner_text()  # Get the text value of x
                return views_no.strip()  # Remove any extra whitespace
            else:
                print(f"Views element not found using selector: {views_selector}")
                return None
        except Exception as e:
            print(f"Error while scraping views number: {e}")
            return None

    async def scrape_id(self, link):
        try:
            # Match the ID from the URL (last part of the URL after the last hyphen)
            match = re.search(r'-(\d+)$', link)
            return match.group(1) if match else None
        except Exception as e:
            print(f"Error while scraping id from link: {e}")
            return None

    async def scrape_image(self, page):
        try:
            image_selector = '.styles_img__PC9G3'
            image = await page.query_selector(image_selector)
            return await image.get_attribute('src') if image else None
        except Exception as e:
            print(f"Error scraping image: {e}")
            return None

        # New method to scrape the price
    async def scrape_price(self, page):
        price_selector = '.h3.m-h5.text-prim_4sale_500'
        price = await page.query_selector(price_selector)
        return await price.inner_text() if price else "0 KWD"

    # New method to scrape the address
    async def scrape_address(self, page):
        address_selector = '.text-4-regular.m-text-5-med.text-neutral_600'
        address = await page.query_selector(address_selector)
        if address:
            text = await address.inner_text()
            # Check if the text matches the format "Ad ID: <any number>"
            if re.match(r'^Ad ID: \d+$', text):
                return "Not Mentioned"
            return text
        return "Not Mentioned"

    # New method to scrape the number of beds
    async def scrape_beds(self, page):
        beds_selector = '.d-flex.align-items-center.bg-neutral_50.styles_attr__BN3w_ img[alt="Rooms"] + div.text-4-med.m-text-5-med.text-neutral_900'
        beds = await page.query_selector(beds_selector)
        return await beds.inner_text() if beds else "0 Bed"

    # New method to scrape the area
    async def scrape_area(self, page):
        area_selector = '.d-flex.align-items-center.bg-neutral_50.styles_attr__BN3w_ img[alt="Property Area"] + div.text-4-med.m-text-5-med.text-neutral_900'
        area = await page.query_selector(area_selector)
        return await area.inner_text() if area else "0 m2"

    async def scrape_extra_specs(self, page):
        selector = '.styles_attrs__PX5Fs .styles_attr__BN3w_'
        elements = await page.query_selector_all(selector)

        attributes = {}
        for element in elements:
            # Extract the alt attribute value from the <img> tag
            img_element = await element.query_selector('img')
            if img_element:
                alt_text = await img_element.get_attribute('alt')

                # Extract the text from the corresponding <div>
                text_element = await element.query_selector('.text-4-med.m-text-5-med.text-neutral_900')
                if text_element:
                    value = await text_element.inner_text()

                    # Add the extracted information to the dictionary
                    if alt_text and value:
                        # Clean up the value if needed
                        attributes[alt_text] = value.strip()

        return attributes

    # New method to scrape the phone number
    async def scrape_phone_number(self, page):
        """
        Extracts the phone number from a JSON object embedded in the page.
        """
        try:
            # Extract the content of the script tag with id="__NEXT_DATA__"
            script_content = await page.inner_html('script#__NEXT_DATA__')

            if script_content:
                # Parse the JSON data from the script content
                data = json.loads(script_content.strip())

                # Navigate through the structure to find the phone number
                phone_number = data.get("props", {}).get("pageProps", {}).get("listing", {}).get("phone", None)

                if phone_number:
                    return phone_number
                else:
                    print("Phone number not found in the JSON structure.")
                    return None
            else:
                print("Script tag with id '__NEXT_DATA__' not found.")
                return None

        except Exception as e:
            print(f"Error while scraping phone number: {e}")
            return None


    # Add new submitter scraping method
    async def scrape_submitter_details(self, page):
        info_wrapper_selector = '.styles_infoWrapper__v4P8_'
        info_wrappers = await page.query_selector_all(info_wrapper_selector)

        if len(info_wrappers) > 0:
            second_div = info_wrappers[0]
            submitter_selector = '.text-4-med.m-h6.text-neutral_900'
            submitter_element = await second_div.query_selector(submitter_selector)
            submitter = await submitter_element.inner_text() if submitter_element else None

            details_selector = '.styles_memberDate__qdUsm span.text-neutral_600'
            detail_elements = await second_div.query_selector_all(details_selector)

            # Extract ads with validation
            if len(detail_elements) > 0:
                ads_text = await detail_elements[0].inner_text()
                ads = ads_text if re.match(r'^\d+\s+ads$', ads_text, re.IGNORECASE) else "0 ads"
            else:
                ads = "0 ads"

            # Extract membership with fallback
            membership = None
            if len(detail_elements) > 1:
                membership_text = await detail_elements[1].inner_text()
                if re.match(r'^Member since .+$', membership_text, re.IGNORECASE):
                    membership = membership_text
                else:
                    # Fallback to the first element if membership is null or does not match
                    membership = await detail_elements[0].inner_text()
            elif len(detail_elements) > 0:
                # Fallback to the first element if no second element exists
                membership = await detail_elements[0].inner_text()

            return {
                'submitter': submitter,
                'ads': ads,
                'membership': membership
            }
        return {}

    # Method to scrape additional details
    # async def scrape_additional_details(self, url):
    #     try:
    #         # Create a new page for this property detail scraping
    #         async with async_playwright() as p:
    #             browser = await p.chromium.launch(headless=True)
    #             page = await browser.new_page()

    #             await page.goto(url, wait_until="domcontentloaded")
    #             await page.wait_for_selector('.StackedCard_card__Kvggc', timeout=300000)

    #             # Extract details using helper methods
    #             image = await self.scrape_image(page)
    #             price = await self.scrape_price(page)
    #             address = await self.scrape_address(page)
    #             beds = await self.scrape_beds(page)
    #             area = await self.scrape_area(page)
    #             specifications = await self.scrape_extra_specs(page)
    #             views_no = await self.scrape_views_no(page)
    #             submitter_details = await self.scrape_submitter_details(page)
    #             phone = await self.scrape_phone_number(page)
    #             relative_date = await self.scrape_relative_date(page)
    #             date_published = await self.scrape_publish_date(relative_date)


    #             # Consolidate details into a dictionary
    #             details = {
    #                 'image': image,
    #                 'price': price,
    #                 'address': address,
    #                 'beds': beds,
    #                 'area': area,
    #                 'specifications': specifications,
    #                 'views_no': views_no,
    #                 'submitter': submitter_details.get('submitter'),
    #                 'ads': submitter_details.get('ads'),
    #                 'membership': submitter_details.get('membership'),
    #                 'phone': phone,
    #                 'relative_date': relative_date,
    #                 'date_published': date_published,
    #             }

    #             await browser.close()
    #             return details

    #     except Exception as e:
    #         print(f"Error while scraping additional details from {url}: {e}")
    #         return {}
    async def scrape_additional_details(self, url):
        if not url:
            print("No URL provided to scrape_additional_details.")
            return {}
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="domcontentloaded")
                # Wait for a selector present on the detail page! Example: main image or title
                await page.wait_for_selector('.styles_img__PC9G3, .h3.m-h5.text-prim_4sale_500', timeout=300000)
                image = await self.scrape_image(page)
                price = await self.scrape_price(page)
                address = await self.scrape_address(page)
                beds = await self.scrape_beds(page)
                area = await self.scrape_area(page)
                specifications = await self.scrape_extra_specs(page)
                views_no = await self.scrape_views_no(page)
                submitter_details = await self.scrape_submitter_details(page)
                phone = await self.scrape_phone_number(page)
                relative_date = await self.scrape_relative_date(page)
                date_published = await self.scrape_publish_date(relative_date)
                details = {
                    'image': image,
                    'price': price,
                    'address': address,
                    'beds': beds,
                    'area': area,
                    'specifications': specifications,
                    'views_no': views_no,
                    'submitter': submitter_details.get('submitter'),
                    'ads': submitter_details.get('ads'),
                    'membership': submitter_details.get('membership'),
                    'phone': phone,
                    'relative_date': relative_date,
                    'date_published': date_published,
                }
                await browser.close()
                return details
        except Exception as e:
            print(f"Error while scraping additional details from {url}: {e}")
            return {}

# # Correctly run the async function with an instance of the class
# if __name__ == "__main__":
#     # Initialize the scraper with the main page URL
#     scraper = DetailsScraping("https://www.q84sale.com/en/property/for-sale/house-for-sale/1")
#
#     # Use asyncio.run to execute the async function
#     properties = asyncio.run(scraper.get_property_details())
#
#     # Print the extracted details
#     for property in properties:
#         print(property)
