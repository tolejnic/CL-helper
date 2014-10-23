# -*- coding: utf-8 -*-
# new color scheme
# #1DBCD0
#
def index():
    import requests
    from random import randint

    #grab proxy list
    f = open('/Users/tim/web2py/applications/cl/static/proxies')
    proxies = f.readlines()
    f.close()

    #set up a random proxy
    r = randint(0, 1500)
    proxy = proxies[r].split(':')
    proxy = {str(proxy[1]): str(proxy[0])}

    #spoof some headers
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip,deflate,sdch",
        "Accept-Language": "en-US,en;q=0.8",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Cookie": "cl_b=Mn-VhVxL5BGDJssYRfy2dg4EAc8; cl_tocmode=ggg%3Alist%2Cjjj%3Alist%2Csss%3Agrid%2Cbbb%3Alist%2Ceee%3Alist; cl_def_lang=en; cl_def_hp=sfbay",
        "Host": "sfbay.craigslist.org",
        "If-Modified-Since": "Fri, 10 Oct 2014 03:11:15 GMT",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.101 Safari/537.36"
    }

    urls = db().select(db.urls.ALL)

    for row in urls:
        url = row.url
        try:
            r = requests.get(url, proxies=proxy, headers=headers)
            new_html = r.text
            old_html = row.raw_html
            #if new html is different
            if compare_html(new_html, row):
                row.update_record(raw_html=new_html)
                new_html = difference(old_html, new_html)
                update_list(new_html)
                #send_sms(new_html)

        except Exception, e:
            return e

    return redirect(URL('default', 'manage'))


def difference(old_html, new_html):
    html = []
    for old, new in zip(str(old_html).split('\n'), str(new_html).split('\n')):
        if new in old:
            pass
        else:
            html.append(new)
    return '\n'.join(list(html))


def compare_html(new_html, row):
    #check for prior entry
    if row.raw_html is not None:
        old_html = row.raw_html
        if old_html == new_html:
            return False
        else:
            return True
    else:
        #if first entry
        row.update_record(raw_html=new_html)
        update_list(new_html)
        return False

def send_sms(new_html):
    from gluon.contrib.sms_utils import SMSCODES, sms_email
    from bs4 import BeautifulSoup
    email = sms_email(db.auth_user[auth.user_id].sms, db.auth_user[auth.user_id].carrier)
    soup = BeautifulSoup(new_html)
    message = []

    for link, url in zip(soup.find_all('p', class_='row'), soup.find_all('a', class_='i')):
        try:
            date = link.get_text().split()
            #date = datetime.datetime.strftime("%m/%d/%Y", +'/2014')
            loc = link.get_text().split("(")
            title = loc[0].split()
            message.append(
                " ".join(title[2:]) + ' (' +\
                loc[-1].split(")")[0] + ')')
        except:
            pass
    return mail.send(to=email, subject = 'new listings', message=' '.join(list(message)))


def update_list(new_html):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(new_html)
    for link, url in zip(soup.find_all('p', class_='row'), soup.find_all('a', class_='i')):
        try:
            date = link.get_text().split()
            #date = datetime.datetime.strftime("%m/%d/%Y", +'/2014')
            loc = link.get_text().split("(")
            title = loc[0].split()
            db.links.insert(
                name=" ".join(title[2:]),
                url=url.get('href'),
                city=loc[-1].split(")")[0],
                created_time=str(date[0] + ' ' + date[1]),
                note=''
            )
        except:
            pass
    return None


def manage():
    #return send_sms('''<p class="row" data-pid="4715828170"> <a href="/nby/web/4715828170.html" class="i"></a> <span class="txt"> <span class="star"></span> <span class="pl"> <time datetime="2014-10-15 09:40" title="Wed 15 Oct 09:40:28 AM (1 days ago)">Oct 15</time>  <a href="/nby/web/4715828170.html" data-id="4715828170" class="hdrlnk">Senior Team Leader:  ePub Development</a> </span> <span class="l2">   <span class="pnr"> <small> (San Fran/Marin )</small> <span class="px"> <span class="p"> </span></span> </span>  </span> </span> </p> ''')
    import re
    tables = []
    urls = db(db.urls.id > 0).select()
    for u in urls:
        url = u.url
        url = re.sub('http://sfbay.craigslist.org/search/', '', url)
        #return url
        query=((db.links.url.contains(url)))
        #db(db.product.colors.contains('red')).select()
        headers = {
            'links.created_time': 'Date',
            'links.city': 'City',
            'links.name': 'Title',
            'links.note': 'Notes',
        }
        fields = (db.links.created_time, db.links.city, db.links.name, db.links.note, db.links.url)

        tables.append(
            SQLFORM.grid(
                query=query,
                headers=headers,
                fields=fields,
                maxtextlength=50,
                paginate=1000,
                deletable=True,
                create=False,
                csv=False,
                details=False,
                searchable=False,
                showbuttontext=False,
                editable=False,
                links=[
                    lambda row: A('view', _href='http://sfbay.craigslist.org' + str(row.url)),
                    lambda row: A('add note', _href=URL("edit_note", args=[row.id]))
                ]
            )
        )

    return dict(tables=tables, urls=urls)


def add_link():
    form = SQLFORM(db.urls)
    if form.process().accepted:
        response.flash = 'URL added'
        return redirect(URL('manage_links'))
    elif form.errors:
        response.flash = 'URL has errors'
    else:
        response.flash = 'please enter a URL'

    return dict(form=form)


def manage_data():
    headers = {
        'raw_html.id': 'ID',
        'raw_html.raw_text': 'Text'
    }

    fields = (db.raw_html.id, db.raw_html.raw_text)

    table = SQLFORM.grid(
        db.raw_html,
        headers=headers,
        fields=fields,
        maxtextlength=100,
        paginate=10,
        deletable=True,
        details=False,
        searchable=False,
        links=[
            lambda row: A('view', _href=URL("view_data", args=[row.id])),
            lambda row: A('delete', _href=URL("delete_raw", args=[row.id]))
        ]
    )
    return dict(table=table)


def manage_links():
    headers = {
        'urls.id': 'ID',
        'urls.url': 'URL'
    }

    fields = (db.urls.id, db.urls.url)

    table = SQLFORM.grid(db.urls,
                         headers=headers,
                         fields=fields,
                         maxtextlength=100,
                         paginate=10,

                         deletable=True,
                         details=False,
                         searchable=False,
                         showbuttontext=False,
                         csv=False,
                         links=[
                             lambda row: A('view', _href=row.url),
                         ]
    )
    return dict(table=table)


def view_data():
    row = db(db.raw_html.id == request.args(0)).select().first()
    return dict(row=row)


def delete():
    crud.delete(db.links, request.args(0), next=URL('manage'))


def edit_note():
    form = crud.update(db.links, request.args(0), next=URL('manage'))
    return dict(form=form)


def delete_link():
    crud.delete(db.urls, request.args(0), next=URL('manage_links'))


def delete_raw():
    crud.delete(db.raw_html, request.args(0), next=URL('manage_data'))


def delete_all():
    db.links.truncate()
    rows = db(db.urls.id > 0).select()
    for row in rows:
        row.update_record(raw_html=None)
    return redirect(URL('manage'))


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())
