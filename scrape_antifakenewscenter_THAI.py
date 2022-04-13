from selenium import webdriver
import selenium.common.exceptions
# from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait 
import os
import time
import json

if __name__=="__main__":
    service = Service(executable_path="geckodriver.exe")
    driver = webdriver.Firefox(service=service)
    dumpdir = "articles"
    labeldict = {0: "real", 1 : "fake", 2:"distorted", 3:"No Label"}
    
    if not os.path.exists("article_list.json"):
        driver.get("https://www.antifakenewscenter.com/allcontent/")
        article_list = []
        idx = 0
        while True:
            time.sleep(2)
            targetlist = driver.find_elements(by=By.CSS_SELECTOR,value="div.blog-container")
            for elements in targetlist:
                try:
                    hyperlink = elements.find_element(by=By.CLASS_NAME,value="blog-img").find_element(by=By.CSS_SELECTOR,value="a").get_attribute("href")
                    title = elements.find_element(by=By.CLASS_NAME,value="blog-title").text
                    container = elements.find_element(by=By.CLASS_NAME,value="blog-tag-container")
                    all_tags = container.find_elements(by= By.CSS_SELECTOR, value="div.blog-tag")
                    additional_tags = []
                    label = None
                    for tag in all_tags:
                        if "tag-status-st-fake" in tag.get_attribute("class"):
                            label = 1
                        elif "tag-status-st-true" in tag.get_attribute("class"):
                            label = 0
                        elif "tag-status-st-distorted" in tag.get_attribute("class"):
                            label = 2
                        else:
                            additional_tags.append(tag.text)
                    if label==None:
                        label = 3
                    # print(hyperlink)
                    # print(label)
                    # print(additional_tags)
                    # print(title)
                    article_list.append({"Hyperlink":hyperlink, "Label":label,"Tags":additional_tags,"Title":title,"ID":idx})
                    idx+=1

                except Exception as e:
                    print(e)
                    pass
            try:
                button = driver.find_element(by=By.CLASS_NAME, value="J-paginationjs-next")
                bottomcoordinates = button.location_once_scrolled_into_view
                driver.execute_script('window.scrollTo({}, {});'.format(bottomcoordinates['x'], bottomcoordinates['y']+50))
                # print(button.get_attribute("class"))
                driver.execute_script("arguments[0].click();", button)
            except selenium.common.exceptions.NoSuchElementException as e:
                print("Seems to be out of pages of links")
                break
            # driver.find_element(by=By.CLASS_NAME,value="J-paginationjs-next").click()
        with open("article_list.json","w",encoding="utf-8") as dumpfile:
            json.dump(article_list,dumpfile,indent=4)
        
    
    if not os.path.isdir(dumpdir):
        os.mkdir(dumpdir)
        
    with open("article_list.json","r",encoding="utf-8") as dumpfile:
        article_list = json.load(dumpfile)
    
    
    
    for article in article_list:
        if os.path.exists(os.path.join(dumpdir,str(article["ID"])+".json")):
            continue
        current_article_dict = {"errors":[]}
        driver.get(article["Hyperlink"])
        date = driver.find_element(by=By.CLASS_NAME, value = "entry-date").get_attribute("datetime")
        current_article_dict["Entry Date"] = date
        overheadtags = driver.find_element(by=By.CLASS_NAME, value = "blog-tag-container")
        divoverheads = overheadtags.find_elements(by=By.CSS_SELECTOR,value = "div")
        aoverheads = overheadtags.find_elements(by=By.CSS_SELECTOR,value = "a")
        
        for div in divoverheads:
            if "tag-status-st-fake" in div.get_attribute("class"):
                label = 1
            elif "tag-status-st-true" in div.get_attribute("class"):
                label = 0
            elif "tag-status-st-distorted" in div.get_attribute("class"):
                label = 2
            else:
                label=3 # lacking a label.
            
        if label==None or label!=article["Label"]:
            current_article_dict["errors"].append("Mismatch/Incorrect Int-Ext Label")
            
        current_article_dict["Internal_Label"] = label
        current_article_dict["External_Label"] = article["Label"]
            
        overheadtag_list = []
        for a in divoverheads:
            subjectname = a.text
            subjecthref = a.get_attribute("href")
            overheadtag_list.append((subjectname,subjecthref))
            
        current_article_dict["Overhead Tags"] = overheadtag_list
        
        
        bottom_taglist = []
        try:
            bottomtags = driver.find_element(by=By.CLASS_NAME, value="tdb-tags")
            
            for tag in driver.find_elements(by=By.CSS_SELECTOR,value="a"):
                bottom_taglist.append((tag.text, tag.get_attribute("href")))
        except selenium.common.exceptions.NoSuchElementException:
            pass
            
        current_article_dict["Bottom Tags"] = bottom_taglist
        
        inspection_agency = driver.find_element(by=By.CLASS_NAME, value="auditcontent")
        current_article_dict["Inspection Agency"] = (inspection_agency.text , inspection_agency.find_element(by=By.CSS_SELECTOR,value = "a").get_attribute("href"))
        
        
        
        post_content = driver.find_element(by=By.CLASS_NAME, value="td-post-content")
        text = post_content.text
        current_article_dict["Article Text"] = text
        
        images = post_content.find_elements(by=By.CSS_SELECTOR,value="img")
        imagelist = []
        for image in images:
            imagelist.append(image.get_attribute("src"))
        current_article_dict["Images"] = imagelist
        
        with open(os.path.join(dumpdir,str(article["ID"])+".json"),"w",encoding="utf-8") as articledumpfile:
            json.dump(current_article_dict,articledumpfile,indent=4)
        
        