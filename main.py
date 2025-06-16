import asyncio
from playwright.async_api import async_playwright
import nest_asyncio
from DetailsScraper import DetailsScraping
import json
import pandas as pd
from datetime import datetime, timedelta
from SavingOnDrive import SavingOnDrive
import os

class MainScraper:
    def __init__(self, categories):
        self.categories = categories  # List of (name, base_url, pages)
        self.results = {}  # Dictionary to store results for each category

    async def scrape_category(self, name, base_url, pages):
        all_properties = []
        # Calculate yesterday's date in 'YYYY-MM-DD' format
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        print(f"Filtering properties published on: {yesterday}")

        for i in range(1, pages + 1):
            url = base_url.format(i)
            print(f"Scraping page: {url} for category: {name}")
            scraper = DetailsScraping(url)
            try:
                properties = await scraper.get_property_details()
                # Filter properties by published_date
                filtered_properties = [
                    prop for prop in properties
                    if 'date_published' in prop and prop['date_published'].split(' ')[0] == yesterday
                ]
                if not filtered_properties:
                    print(f"No properties found on page {i} for category {name} with the specified date.")
                all_properties.extend(filtered_properties)
            except Exception as e:
                print(f"Error scraping {url}: {e}")

        if all_properties:
            self.results[name] = all_properties
        else:
            print(f"No data collected for category {name}.")
    
    async def run(self):
        tasks = []
        for name, base_url, pages in self.categories:
            tasks.append(self.scrape_category(name, base_url, pages))
        await asyncio.gather(*tasks)

    def save_to_excel(self, file_name):
        try:
            with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
                for name, properties in self.results.items():
                    if properties:  # Only save sheets with data
                        df = pd.DataFrame(properties)
                        df.to_excel(writer, sheet_name=name, index=False)
                        print(f"Data for '{name}' saved to Excel.")
            print(f"All data successfully saved to {file_name}.")
        except PermissionError:
            print(f"Error: Unable to save the file '{file_name}'. It may be open in another application.")
            backup_file_name = file_name.replace('.xlsx', '_backup.xlsx')
            print(f"Attempting to save data to '{backup_file_name}' instead.")
            try:
                with pd.ExcelWriter(backup_file_name, engine='openpyxl') as writer:
                    for name, properties in self.results.items():
                        if properties:
                            df = pd.DataFrame(properties)
                            df.to_excel(writer, sheet_name=name, index=False)
                            print(f"Data for '{name}' saved to backup file.")
                print(f"All data successfully saved to {backup_file_name}.")
            except Exception as e:
                print(f"Failed to save to backup file: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while saving to Excel: {e}")

# --- NEW CODE: Helper function to scrape categories_1 automatically ---
async def get_categories_1():
    url = "https://www.q84sale.com/en/property/for-sale/1"
    categories = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print(f"Going to main for-sale page: {url}")
        await page.goto(url, wait_until='domcontentloaded')

        # Grab all category anchors
        category_anchors = await page.query_selector_all('section.styles_section__10hLu a.styles_link__Pf9GR')
        print(f"Found {len(category_anchors)} category anchors.")

        anchor_infos = []
        for idx, anchor in enumerate(category_anchors):
            title = await anchor.get_attribute('title')
            link = await anchor.get_attribute('href')
            print(f"Anchor {idx}: title={title!r}, link={link!r}")
            if title and link:
                anchor_infos.append((title, link))

        # Now check number of pages for each
        for idx, (title, link) in enumerate(anchor_infos):
            base_url = "https://www.q84sale.com" + link
            print(f"\nChecking category: {title} at {base_url}")
            pages = 0
            for i in range(1, 6):
                check_url = base_url.replace('/1', f'/{i}')
                print(f"  Checking page {i}: {check_url}")
                try:
                    resp = await page.goto(check_url, wait_until='domcontentloaded')
                    status = resp.status
                except Exception as e:
                    print(f"    Error loading page {i}: {e}")
                    status = 404
                if status == 200:
                    pages = i
                else:
                    print(f"    Page {i} not found (status {status}), stopping at {pages} pages.")
                    break
            if pages > 0:
                print(f"  --> Category '{title}' has {pages} pages.")
                categories.append((title, base_url.replace('/1', '/{}'), pages))
            else:
                print(f"  --> Category '{title}' has no accessible pages, skipping.")

        print("\nFinal categories_1 list:")
        for cat in categories:
            print(cat)
        await browser.close()
    return categories

if __name__ == "__main__":
    nest_asyncio.apply()  # Ensure compatibility with nested event loops

    # Define the scraping categories
    # categories_1 = [ ... ]  # <-- REMOVE THIS BLOCK
    categories_1 = asyncio.run(get_categories_1())  # <-- AUTO SCRAPE CATEGORIES

    categories_2 = [
        ("House for Rent", "https://www.q84sale.com/en/property/for-rent/house-for-rent/{}", 2),
        ("Floor", "https://www.q84sale.com/en/property/for-rent/floor/{}", 2),
        ("Furnished Apartment", "https://www.q84sale.com/en/property/for-rent/furnished-apartment/{}", 1),
        ("Apartment For Rent", "https://www.q84sale.com/en/property/for-rent/apartment-for-rent/{}", 7),
        ("Duplex", "https://www.q84sale.com/en/property/for-rent/duplex/{}", 1),
        ("House Sharing", "https://www.q84sale.com/en/property/for-rent/house-sharing/{}", 1),
        ("Shop For Rent", "https://www.q84sale.com/en/property/for-rent/shop-for-rent/{}", 1),
        ("Office", "https://www.q84sale.com/en/property/for-rent/office/{}", 1),
        ("Stores", "https://www.q84sale.com/en/property/for-rent/stores/{}", 1),
        ("Farms For Rent", "https://www.q84sale.com/en/property/for-rent/farms-for-rent/{}", 2),
        ("Lounge For Rent", "https://www.q84sale.com/en/property/for-rent/lounge-for-rent/{}", 2),
        ("Industrial Certificate", "https://www.q84sale.com/en/property/for-rent/industrial-certificate/{}", 1),
        ("Chalet For Rent", "https://www.q84sale.com/en/property/for-rent/chalet-for-rent/{}", 2),
        ("Rental Playgrounds", "https://www.q84sale.com/en/property/for-rent/rental-playgrounds/{}", 1),
        ("Wanted Property for Rent", "https://www.q84sale.com/en/property/for-rent/wanted-property-for-rent/{}", 1),
    ]

    categories_3 = [
        ("Property For Exchange", "https://www.q84sale.com/en/property/for-exchange/{}", 2),
    ]

    # Create an instance of the scraper
    PropertyForSale_scraper = MainScraper(categories_1)
    PropertyForRent_scraper = MainScraper(categories_2)
    PropertyForExchange_scraper = MainScraper(categories_3)

    # Run the scraper
    asyncio.run(PropertyForSale_scraper.run())
    asyncio.run(PropertyForRent_scraper.run())
    asyncio.run(PropertyForExchange_scraper.run())

    # Save all results to an Excel file
    excel_file_name_1 = "Property for Sale.xlsx"
    excel_file_name_2 = "Property for Rent.xlsx"
    excel_file_name_3 = "Property For Exchange.xlsx"

    PropertyForSale_scraper.save_to_excel(excel_file_name_1)
    PropertyForRent_scraper.save_to_excel(excel_file_name_2)
    PropertyForExchange_scraper.save_to_excel(excel_file_name_3)

    # Load the service account JSON key from the GitHub secret
    credentials_json = os.environ.get('GCLOUD_KEY_JSON')
    if not credentials_json:
        raise EnvironmentError("GCLOUD_KEY_JSON environment variable not found.")

    credentials_dict = json.loads(credentials_json)

    # Google Drive credentials file
    # credentials_file = "credentials/real-estate-property-scraper-b7b91306c0e0.json"

    # Initialize the SavingOnDrive class
    drive_saver = SavingOnDrive(credentials_dict)
    drive_saver.authenticate()

    # List of files to save
    excel_files = [excel_file_name_1, excel_file_name_2, excel_file_name_3] # 

    # Save files to Google Drive
    drive_saver.save_files(excel_files)




# import asyncio
# from playwright.async_api import async_playwright
# import nest_asyncio
# from DetailsScraper import DetailsScraping
# import json
# import pandas as pd
# from datetime import datetime, timedelta
# from SavingOnDrive import SavingOnDrive
# import os

# class MainScraper:
#     def __init__(self, categories):
#         self.categories = categories  # List of (name, base_url, pages)
#         self.results = {}  # Dictionary to store results for each category

#     async def scrape_category(self, name, base_url, pages):
#         all_properties = []
#         # Calculate yesterday's date in 'YYYY-MM-DD' format
#         yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
#         print(f"Filtering properties published on: {yesterday}")

#         for i in range(1, pages + 1):
#             url = base_url.format(i)
#             print(f"Scraping page: {url} for category: {name}")
#             scraper = DetailsScraping(url)
#             try:
#                 properties = await scraper.get_property_details()
#                 # Filter properties by published_date
#                 filtered_properties = [
#                     prop for prop in properties
#                     if 'date_published' in prop and prop['date_published'].split(' ')[0] == yesterday
#                 ]
#                 if not filtered_properties:
#                     print(f"No properties found on page {i} for category {name} with the specified date.")
#                 all_properties.extend(filtered_properties)
#             except Exception as e:
#                 print(f"Error scraping {url}: {e}")

#         if all_properties:
#             self.results[name] = all_properties
#         else:
#             print(f"No data collected for category {name}.")
    
#     async def run(self):
#         tasks = []
#         for name, base_url, pages in self.categories:
#             tasks.append(self.scrape_category(name, base_url, pages))
#         await asyncio.gather(*tasks)

#     def save_to_excel(self, file_name):
#         try:
#             with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
#                 for name, properties in self.results.items():
#                     if properties:  # Only save sheets with data
#                         df = pd.DataFrame(properties)
#                         df.to_excel(writer, sheet_name=name, index=False)
#                         print(f"Data for '{name}' saved to Excel.")
#             print(f"All data successfully saved to {file_name}.")
#         except PermissionError:
#             print(f"Error: Unable to save the file '{file_name}'. It may be open in another application.")
#             backup_file_name = file_name.replace('.xlsx', '_backup.xlsx')
#             print(f"Attempting to save data to '{backup_file_name}' instead.")
#             try:
#                 with pd.ExcelWriter(backup_file_name, engine='openpyxl') as writer:
#                     for name, properties in self.results.items():
#                         if properties:
#                             df = pd.DataFrame(properties)
#                             df.to_excel(writer, sheet_name=name, index=False)
#                             print(f"Data for '{name}' saved to backup file.")
#                 print(f"All data successfully saved to {backup_file_name}.")
#             except Exception as e:
#                 print(f"Failed to save to backup file: {e}")
#         except Exception as e:
#             print(f"An unexpected error occurred while saving to Excel: {e}")



# if __name__ == "__main__":
#     nest_asyncio.apply()  # Ensure compatibility with nested event loops

#     # Define the scraping categories
#     categories_1 = [
#         ("House for Sale", "https://www.q84sale.com/en/property/house-for-sale/{}", 5),
#         ("Building or floors", "https://www.q84sale.com/en/property/building-or-floors/{}", 1),
#         ("Apartment for Sale", "https://www.q84sale.com/en/property/apartment-for-sale/{}", 2),
#         ("Demolishing", "https://www.q84sale.com/en/property/demolishing/{}", 1),
#         ("Lounge for Sale", "https://www.q84sale.com/en/property/lounge-for-sale/{}", 1),
#         ("Chalet for Sale", "https://www.q84sale.com/en/property/chalet-for-sale/{}", 1),
#         ("Farms for Sale", "https://www.q84sale.com/en/property/farms-for-sale/{}", 1),
#         ("Land", "https://www.q84sale.com/en/property/land/{}", 1),
#         ("Residential Certificate", "https://www.q84sale.com/en/property/residential-certificate/{}", 1),
#         ("Commercial Land Certificate", "https://www.q84sale.com/en/property/commercial-land-certificate/{}", 1),
#         ("Shop for Sale", "https://www.q84sale.com/en/property/shop-for-sale/{}", 2),
#         ("Company", "https://www.q84sale.com/en/property/company/{}", 1),
#         ("Wanted Property for Sale", "https://www.q84sale.com/en/property/wanted-property-for-sale/{}", 1),
#     ]

#     categories_2 = [
#         ("House for Rent", "https://www.q84sale.com/en/property/for-rent/house-for-rent/{}", 2),
#         ("Floor", "https://www.q84sale.com/en/property/for-rent/floor/{}", 2),
#         ("Furnished Apartment", "https://www.q84sale.com/en/property/for-rent/furnished-apartment/{}", 1),
#         ("Apartment For Rent", "https://www.q84sale.com/en/property/for-rent/apartment-for-rent/{}", 7),
#         ("Duplex", "https://www.q84sale.com/en/property/for-rent/duplex/{}", 1),
#         ("House Sharing", "https://www.q84sale.com/en/property/for-rent/house-sharing/{}", 1),
#         ("Shop For Rent", "https://www.q84sale.com/en/property/for-rent/shop-for-rent/{}", 1),
#         ("Office", "https://www.q84sale.com/en/property/for-rent/office/{}", 1),
#         ("Stores", "https://www.q84sale.com/en/property/for-rent/stores/{}", 1),
#         ("Farms For Rent", "https://www.q84sale.com/en/property/for-rent/farms-for-rent/{}", 2),
#         ("Lounge For Rent", "https://www.q84sale.com/en/property/for-rent/lounge-for-rent/{}", 2),
#         ("Industrial Certificate", "https://www.q84sale.com/en/property/for-rent/industrial-certificate/{}", 1),
#         ("Chalet For Rent", "https://www.q84sale.com/en/property/for-rent/chalet-for-rent/{}", 2),
#         ("Rental Playgrounds", "https://www.q84sale.com/en/property/for-rent/rental-playgrounds/{}", 1),
#         ("Wanted Property for Rent", "https://www.q84sale.com/en/property/for-rent/wanted-property-for-rent/{}", 1),
#     ]

#     categories_3 = [
#         ("Property For Exchange", "https://www.q84sale.com/en/property/for-exchange/{}", 2),
#     ]

#     # Create an instance of the scraper
#     PropertyForSale_scraper = MainScraper(categories_1)
#     PropertyForRent_scraper = MainScraper(categories_2)
#     PropertyForExchange_scraper = MainScraper(categories_3)


#     # Run the scraper
#     asyncio.run(PropertyForSale_scraper.run())
#     asyncio.run(PropertyForRent_scraper.run())
#     asyncio.run(PropertyForExchange_scraper.run())

#     # Save all results to an Excel file
#     excel_file_name_1 = "Property for Sale.xlsx"
#     excel_file_name_2 = "Property for Rent.xlsx"
#     excel_file_name_3 = "Property For Exchange.xlsx"

#     PropertyForSale_scraper.save_to_excel(excel_file_name_1)
#     PropertyForRent_scraper.save_to_excel(excel_file_name_2)
#     PropertyForExchange_scraper.save_to_excel(excel_file_name_3)


#     # Load the service account JSON key from the GitHub secret
#     credentials_json = os.environ.get('GCLOUD_KEY_JSON')
#     if not credentials_json:
#         raise EnvironmentError("GCLOUD_KEY_JSON environment variable not found.")

#     credentials_dict = json.loads(credentials_json)

#     # Google Drive credentials file
#     # credentials_file = "credentials/real-estate-property-scraper-b7b91306c0e0.json"

#     # Initialize the SavingOnDrive class
#     drive_saver = SavingOnDrive(credentials_dict)
#     drive_saver.authenticate()

#     # List of files to save
#     excel_files = [excel_file_name_1, excel_file_name_2, excel_file_name_3] # 

#     # Save files to Google Drive
#     drive_saver.save_files(excel_files)

