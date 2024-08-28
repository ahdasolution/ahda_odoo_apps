from collections import OrderedDict
from ipaddress import ip_address
import json
from lib2to3.pgen2 import driver
from odoo import _, api, fields, models,http
from dateutil import relativedelta
from datetime import date, datetime, timedelta
from odoo.exceptions import Warning
from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from odoo_intranet.lme_nickel_price.models.nickel_price import nickel_price

driver_container = {}

class selenium_server(models.Model):
    _name = 'selenium.server'
    _rec_name = 'selenium_host'

    selenium_host = fields.Char('Selenium Host',required=True)
    browser_type = fields.Selection([('chrome','Chrome'),('firefox','Firefox')],'Browser Type',required=True, )
    max_session = fields.Integer('Max Session',compute="get_state")
    state = fields.Char('Status',compute="get_state")

    def close_all_driver(self):
        host = self.selenium_host
        if host:
            active_nodes = requests.get(host+'/status')
            for node in active_nodes.json()['value']['nodes']:
                for slot in node.get('slots',[]):
                    if slot['session']:
                        session_id = slot['session']['sessionId']
                        requests.delete(host+"/session/"+session_id)


    def get_state(self):
        for rec in self:
            rec.state = 'Disconnected (please check selenium server host)'
            rec.max_session = 0
            if rec.selenium_host:
                code = False
                try:
                    res = requests.get(rec.selenium_host+'/status')
                    code = res.status_code
                    for node in res.json().get('value',{}).get('nodes',[]):
                        rec.max_session = node.get('maxSessions')
                except:
                    pass
                if code == 200:
                    rec.state = 'Connected'

    
class web_scraper(models.Model):
    _name = 'web.scraper'
    _rec_name = 'url'

    def get_python_code_guide(self):
        return """# available variable: driver
# example:
# getting price from https://www.lme.com/Metals/Non-ferrous/LME-Aluminium
price_container = self.driver.find_element(By.CLASS_NAME, 'hero-metal-data__number')
if price_container:
    price = float(price_container.text)
self.print=str(price)"""

    server_id = fields.Many2one('selenium.server','Selenium Server',required=True, )
    url = fields.Char('URL',required=True)
    selenium_host = fields.Char('Selenium Host',related="server_id.selenium_host")
    browser_type = fields.Selection([('chrome','Chrome'),('firefox','Firefox')],'Browser Type',related="server_id.browser_type")
    python_code = fields.Text('Python Code')
    method_guide = fields.Text(default=get_python_code_guide)
    cron_id = fields.Many2one('ir.cron','Cron')
    html_source = fields.Text("HTML Source")
    print = fields.Text('Print',store=True,readonly=True)
    driver = None
    auto_run = fields.Boolean("Auto run")
    interval_number = fields.Integer(default=1, help="Repeat every x.")
    interval_type = fields.Selection([('minutes', 'Minutes'),
                                      ('hours', 'Hours'),
                                      ('days', 'Days'),
                                      ('weeks', 'Weeks'),
                                      ('months', 'Months')], string='Interval Unit', default='months')
    nextcall = fields.Datetime(string='Next Running Date', required=True, default=fields.Datetime.now, help="Next planned execution date for this job.")
    session_id = fields.Char('Session ID')
    html_preview = fields.Html(sanitize=False,compute="get_html_preview")

    @api.depends('html_source')
    def get_html_preview(self):
        for rec in self:
            rec.html_preview = False
            if rec.html_source:
                html = rec.html_source.replace('"','&quot;')
                rec.html_preview = """<iframe srcdoc="%s"></iframe>"""%html


    def unlink(self):
        for rec in self:
            if rec.cron_id:
                rec.cron_id.unlink()
        return super(web_scraper,self).unlink()


    @api.constrains('auto_run','interval_number','interval_type','nextcall')
    def update_cron(self):
        self = self.sudo()
        for rec in self:
            if rec.auto_run:
                vals = {
                        'name' : f'web_scraper_{rec.id}',
                        'interval_number' : rec.interval_number,
                        'interval_type' : rec.interval_type,
                        'numbercall' : '-1',
                        'nextcall' : rec.nextcall,
                        'state' : 'code',
                        'code' : f'model.schedule_scrape({rec.id})',
                        'model_id' : self.env.ref('ahda_selenium_scraper.model_web_scraper').id,
                        'active' : True,
                    }
                if not rec.cron_id:
                    rec.cron_id = self.env['ir.cron'].create(vals)
                else:
                    rec.cron_id.write(vals)
            else:
                if rec.cron_id:
                    rec.cron_id.active = False

    # def get_driver(self):
    #     active_session_ids = []
    #     active_nodes = requests.get(self.selenium_host+'/status')
    #     for node in active_nodes.json()['value']['nodes']:
    #         for slot in node.get('slots',[]):
    #             if slot['session']:
    #                 session_id = slot['session']['sessionId']
    #                 if session_id not in driver_container.keys():
    #                     requests.delete(self.selenium_host+"/session/"+session_id)
    #                 else:
    #                     active_session_ids.append(session_id)

    #     if driver_container:
    #         for session_id in driver_container.keys():
    #             browser = self.search([('session_id','=',session_id)])
    #             if driver_container[session_id].session_id not in active_session_ids or not browser:
    #                 requests.delete(self.selenium_host+"/session/"+session_id)
    #     #         else:
    #     #             active_driver[session_id] = driver_container[session_id]
    #     # driver_container = active_driver
        
    #     driver = driver_container.get(self.session_id)
    #     if not driver:
    #         if len(driver_container) >= self.server_id.max_session:
    #             session_id = next(iter(driver_container))
    #             driver = driver_container[session_id]
    #             self.session_id = session_id
    #         else:
    #             if self.browser_type == 'chrome':
    #                 options = webdriver.ChromeOptions()
    #             else:
    #                 options = webdriver.FirefoxOptions()
                    
    #             driver = webdriver.Remote(
    #                     command_executor=self.selenium_host,
    #                     options=options
    #                 )
    #             driver_container[driver.session_id] = driver
    #             self.session_id = driver.session_id
    #     return driver

    def get_driver(self):
        if self.browser_type == 'chrome':
            options = webdriver.ChromeOptions()
        else:
            options = webdriver.FirefoxOptions()
            
        driver = webdriver.Remote(
                command_executor=self.selenium_host,
                options=options
            )
        self.session_id = driver.session_id
        return driver

    def load_page(self):
        self.driver = self.get_driver()
        url = False
        url_script = f"""
url = f"{self.url}"
self.driver.get(url)
        """
        exec(url_script.strip())
        self.html_source = self.driver.page_source
        return self.driver


    def run_python_code(self):
        self.load_page()
        # try:
        exec(self.python_code.strip())
        self.driver.quit()
        # except:
        #    raise Warning('Wrong code, please check python code again!')

    @api.model
    def schedule_scrape(self,id):
        self = self.browse(id)
        self.run_python_code()

        # except:
        #    raise Warning('Wrong code, please check python code again!')