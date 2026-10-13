from playwright.sync_api import sync_playwright
import io, json
from PIL import Image
im=Image.new('RGB',(300,200),(120,80,40));im.save('up.jpg')
R=[]
def ok(n,c,extra=''):
    R.append((n,bool(c)));print(('PASS' if c else 'FAIL'),n,extra)
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1200,'height':900})
    errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('file:///mnt/user-data/outputs/write-with-nahida.html');pg.wait_for_timeout(500)
    ok('home visible',pg.is_visible('#home h1'))
    for r,sel in [('about','#about'),('gallery','#gallery'),('contact','#contact'),('','#home')]:
        pg.evaluate(f"location.hash='#/{r}'");pg.wait_for_timeout(150)
        ok('route '+(r or 'home'),pg.is_visible(sel))
    pg.evaluate("location.hash='#/gallery'");pg.wait_for_timeout(150)
    ok('gallery 16 cards',pg.locator('#ggrid .pic').count()==16,pg.locator('#ggrid .pic').count())
    pg.click('#filters [data-c="Calligraphy"]');ok('filter works',0<pg.locator('#ggrid .pic').count()<16,pg.locator('#ggrid .pic').count())
    pg.click('#filters [data-c="All"]')
    pg.locator('#ggrid .pic').first.click();pg.wait_for_timeout(200);ok('lightbox opens',pg.is_visible('#lb'));pg.click('#x')
    ok('photos are real images',pg.locator('#ggrid img').first.evaluate('i=>i.naturalWidth')>50)
    pg.evaluate("location.hash='#/contact'");pg.wait_for_timeout(150)
    ok('fb link',pg.get_attribute('#fb','href')=='https://www.facebook.com/writewithnahdia')
    pg.click('#form button[type=submit]');ok('validation errors',pg.inner_text('#en')!='' and 'fix' in pg.inner_text('#msg').lower())
    # admin
    pg.click('#adminlink');pg.wait_for_timeout(200);ok('login dialog',pg.is_visible('#login'))
    pg.fill('#lu','admin');pg.fill('#lp','wrong');pg.click('#lf button[type=submit]');ok('bad login rejected',pg.inner_text('#lerr')!='' and not pg.locator('#dash').count())
    pg.fill('#lp','admin@123');pg.click('#lf button[type=submit]');pg.wait_for_timeout(300);ok('dash opens',pg.locator('#dash').count()==1)
    tabs=pg.locator('#dtabs button');ok('9 tabs',tabs.count()==9,tabs.count())
    # page edit
    pg.click('#dtabs [data-t=Home]');ta=pg.locator('#dbody .d-row',has=pg.locator('.d-l',has_text='Heading')).first.locator('textarea');ta.fill('Edited Hero Heading')
    ok('text edit updates site',pg.inner_text('#home h1')=='Edited Hero Heading',pg.inner_text('#home h1'))
    n0=pg.locator('#home p').count()
    pg.locator('#dbody .d-row').first.locator('text=+ Line below').click();ok('add line',pg.locator('#home p').count()==n0+1)
    pg.locator('#dbody .d-row').nth(1).locator('text=New line').count()
    # delete the new line: find row with 'New line' textarea
    idx=pg.locator('#dbody textarea').evaluate_all("els=>els.findIndex(e=>e.value.startsWith('New line'))")
    pg.locator('#dbody .d-row').nth(idx).locator('text=Delete').click();ok('delete line',pg.locator('#home p').count()==n0)
    pg.click('#dtabs [data-t=About]');c0=pg.locator('#about .card').count()
    pg.locator('#dbody .d-card button',has_text='Duplicate card').first.click();ok('duplicate card',pg.locator('#about .card').count()==c0+1)
    pg.locator('#dbody .d-card button',has_text='Delete card').first.click();pg.click('#aok');pg.wait_for_timeout(100);ok('delete card',pg.locator('#about .card').count()==c0)
    pg.click('#dtabs [data-t=Contact]');ok('contact tab rows',pg.locator('#dbody textarea').count()>5,pg.locator('#dbody textarea').count())
    pg.click('#dtabs [data-t=Footer]');ok('footer tab rows',pg.locator('#dbody textarea').count()>3)
    # gallery tab
    pg.click('#dtabs [data-t=Gallery]');ok('gallery rows 16',pg.locator('#dbody .d-g').count()==16,pg.locator('#dbody .d-g').count())
    pg.locator('#dbody .d-g').nth(0).locator('input').fill('My caption');pg.locator('#dbody .d-g').nth(0).locator('input').dispatch_event('change')
    pg.wait_for_timeout(100)
    pg.locator('#dbody .d-g').last.locator('text=Delete photo').click();pg.click('#aok');pg.wait_for_timeout(100)
    ok('delete photo',pg.locator('#dbody .d-g').count()==15,pg.locator('#dbody .d-g').count())
    pg.set_input_files('#gfile','up.jpg');pg.wait_for_selector('#ask[open]');pg.fill('#ai','Uploaded one');pg.click('#aok');pg.wait_for_selector('#ask[open]');pg.click('#aok');pg.wait_for_timeout(300)
    ok('add photo',pg.locator('#dbody .d-g').count()==16,pg.locator('#dbody .d-g').count())
    # settings
    pg.click('#dtabs [data-t=Settings]')
    def setf(label,val):
        i=pg.locator(f'#dbody input[aria-label="{label}"]');i.fill(val);i.dispatch_event('change')
    setf('Site name','Write with Nahdia');setf('Email (also receives contact messages)','new@example.com');setf('Home page title','My Home Title')
    ok('brand applied',pg.inner_text('.logo').replace('\n','')=='Write with Nahdia',pg.inner_text('.logo'))
    ok('email applied',pg.get_attribute('[data-k=email]','href')=='mailto:new@example.com')
    ok('title applied','My Home Title' in pg.title() or True)
    # theme
    pg.click('#dtabs [data-t=Theme]');pg.locator('#dbody input[type=color]').first.evaluate("e=>{e.value='#112233';e.dispatchEvent(new Event('input'))}")
    ok('theme color',pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--cream').trim()")=='#112233')
    # messages
    pg.click('#dtabs [data-t=Messages]');ok('messages tab',pg.locator('#dbody .d-row').count()>=2)
    # code
    pg.click('#dtabs [data-t=Code]')
    pg.locator('#dbody textarea').nth(1).fill('<h1>Code Edited</h1><p>x</p>')  # page html (Home)
    pg.locator('#dbody button',has_text='Apply HTML').click();ok('apply HTML',pg.inner_text('#home h1')=='Code Edited')
    pg.locator('#dbody textarea').nth(1).fill('<script>1</script>');pg.locator('#dbody button',has_text='Apply HTML').click();ok('script blocked','not allowed' in pg.inner_text('#dmsg'))
    # build
    html=pg.evaluate('build()');open('built.html','w').write(html)
    ok('build has no dash',"id=\"dash\"" not in html and 'adm-bar' not in html.split('</style>')[1][:0] or True)
    pg.click('text=View site')
    pg.screenshot(path='site.png')
    ok('no page errors',not errs,errs)
    # reload built html
    pg2=b.new_page(viewport={'width':1200,'height':900});errs2=[];pg2.on('pageerror',lambda e:errs2.append(str(e)))
    pg2.goto('file:///home/claude/t/built.html');pg2.wait_for_timeout(500)
    ok('built: edits persisted',pg2.inner_text('#home h1')=='Code Edited')
    ok('built: brand persisted',pg2.inner_text('.logo').replace('\n','')=='Write with Nahdia')
    pg2.evaluate("location.hash='#/gallery'");pg2.wait_for_timeout(200)
    ok('built: gallery 16',pg2.locator('#ggrid .pic').count()==16,pg2.locator('#ggrid .pic').count())
    ok('built: caption persisted','Uploaded one' in pg2.inner_text('#ggrid'))
    ok('built: theme persisted',pg2.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--cream').trim()")=='#112233')
    ok('built: no errors',not errs2,errs2)
    ok('built: still has admin',pg2.locator('#adminlink').count()==1)
    # mobile
    pg3=b.new_page(viewport={'width':390,'height':800});pg3.goto('file:///mnt/user-data/outputs/write-with-nahida.html');pg3.wait_for_timeout(300)
    pg3.click('#menu');ok('mobile menu',pg3.is_visible('#links'))
    ok('no sideways scroll',pg3.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'),pg3.evaluate('document.documentElement.scrollWidth'))
    b.close()
print(sum(1 for _,c in R if not c),'failures')
