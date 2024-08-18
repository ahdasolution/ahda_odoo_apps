from odoo import _, api, fields, models,http
from dateutil import relativedelta
from datetime import date, datetime
import dryscrape
from odoo.exceptions import Warning

class web_scraper(models.Model):
    _name = 'web.scraper'
    _rec_name = 'url'

    def get_python_code_guide(self):
        return """# available variable: session
# example:
# getting price from https://www.lme.com/Metals/Non-ferrous/LME-Aluminium
# price_container = self.session.at_xpath('//span[@class="hero-metal-data__number"]')
# price = 0
# if price_container:
#     price = float(price_container.text())
# self.print=str(price)"""

    url = fields.Char('URL',required=True)
    python_code = fields.Text('Python Code')
    method_guide = fields.Text(default=get_python_code_guide)
    cron_id = fields.Many2one('ir.cron','Cron')
    html_source = fields.Text("HTML Source")
    print = fields.Text('Print',store=True,readonly=True)
    stored_session = False
    session = fields.Binary(compute="load_page")
    auto_run = fields.Boolean("Auto run")
    interval_number = fields.Integer(default=1, help="Repeat every x.")
    interval_type = fields.Selection([('minutes', 'Minutes'),
                                      ('hours', 'Hours'),
                                      ('days', 'Days'),
                                      ('weeks', 'Weeks'),
                                      ('months', 'Months')], string='Interval Unit', default='months')
    nextcall = fields.Datetime(string='Next Running Date', required=True, default=fields.Datetime.now, help="Next planned execution date for this job.")


    def unlink(self):
        for rec in self:
            rec.cron_id.unlink()
        return super(web_scraper,self).unlink()


    @api.constrains('auto_run','interval_number','interval_type','nextcall')
    def update_cron(self):
        self = self.sudo()
        for rec in self:
            if rec.auto_run:
                rec.cron_id = self.env['ir.cron'].create({
                    'name' : f'web_scraper_{rec.id}',
                    'interval_number' : rec.interval_number,
                    'interval_type' : rec.interval_type,
                    'numbercall' : '-1',
                    'nextcall' : rec.nextcall,
                    'state' : 'code',
                    'code' : f'model.schedule_scrape({rec.id})',
                    'model_id' : self.env.ref('ahda_web_scraper.model_web_scraper').id,
                    'active' : True,
                })
            else:
                if rec.cron_id:
                    rec.cron_id.active = False

    def load_page(self):
        if self.stored_session:
            self.session = self.stored_session
        else:
            # if 'linux' in sys.platform:
            #     # start xvfb in case no X is running. Make sure xvfb 
            #     # is installed, otherwise this won't work!
            #     dryscrape.start_xvfb()
            session = dryscrape.Session()
            self.session = session
            self.stored_session = session
        self.session.visit(self.url)
        self.html_source = session.body()

    def run_python_code(self,id=None):
        if id:
            self = self.browse(id)
        self.print = False
        try:
            exec(self.python_code.strip())
        except:
           raise Warning('Wrong code, please check python code again!')

    @api.model
    def schedule_scrape(self,id):
        self = self.browse(id)
        self.print = False
        try:
            exec(self.python_code.strip())
        except:
           raise Warning('Wrong code, please check python code again!')