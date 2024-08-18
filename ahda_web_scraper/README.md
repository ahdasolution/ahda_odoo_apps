AHDA Web Scraper  

===================

This module allows you to scrape a website and do something in odoo with the data. Usually you will scrape a website that does not provide an api service. This module uses the python library "dryscrape" created by nikslab, for more information visit [http://dryscrape.readthedocs.io/](http://dryscrape.readthedocs.io/). Python technical skills will be required to use this module optimally  

* * *

*   **URL**: the url of the website to be scraped
*   **Python Code**: The code to be executed after the web page is loaded. You can do anything here. For example: you want to get the price/rate from a website, then you want to record it to a model in odoo. You can test your python code by printing the result. self.session is a drysrape object that has loaded the url. You just need to find the target tag with the method provided by drysacrape. For more information please check [http://dryscrape.readthedocs.io/](http://dryscrape.readthedocs.io/) The code example is provided in the view form
*   **Auto run**: if you want to schedule the scraping, you can check this, then set the interval and date to run. This will automatically generate a cron job

*   **HTML Source**: the html source of the loaded url. This will help you find the attributes  
    
* * *

  
Contact me for Support, Customization, Implementation:  
**Email**: [ariehariady@gmail.com  
](mailto:ariehariady@gmail.com)**linkedIn**: [https://www.linkedin.com/in/ariehariady](https://www.linkedin.com/in/ariehariady)
