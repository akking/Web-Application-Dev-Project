# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
#########################################################################

def text():
    return 'helloworld'


def index():
    # if auth.is_logged_in():
    #     response.menu=None
    # else:
    #     response.menu = [
    #         (T('Home'), False, URL('default', 'index'), [])
    #     ]
    featured_items = db().select(db.item.ALL, orderby='<random>')
    featured_shop = db().select(db.shop.ALL, orderby='<random>')
    return dict(shop=featured_shop, items=featured_items, message=T('Welcome to etsy!'))


@auth.requires_login()
def newlisting():
    user = db(db.auth_user.id == auth.user_id).select().first()
    if user.is_seller:
        shop = db(db.shop.shop_owner == user.id).select().first()
        db.item.shop_name.default = shop.id
        db.item.shop_name.readable = False
        db.item.shop_name.writable = False
        form = SQLFORM(db.item)
        if form.process().accepted:
            session.flash = 'New listing created!'
            redirect(URL('shop', args=shop.id))
        return dict(form=form)
    else:
        session.flash = "You don't have shop yes, please open one."
        redirect(URL('index'))


def listing():
    item_id = request.args(0, cast=int) or redirect(URL('index'))
    item = db.item(item_id)
    seller = db(db.auth_user.id == item.created_by).select().first()
    return dict(item=item, seller=seller)


@auth.requires_login()
def buy():
    item_id = request.args(0, cast=int) or redirect(URL('index'))
    buyer = auth.user_id
    db.cart.insert(buyer=buyer, item=item_id)
    session.flash = 'Shopping cart updated!'
    redirect(URL('listing', args=item_id))
    return


@auth.requires_login()
def ask():
    item_id = request.args(0, cast=int) or redirect(URL('index'))
    asker = auth.user_id
    seller = db(db.item.id == item_id).select().first().created_by
    db.communication.item.default = item_id
    db.communication.buyer.default = asker
    db.communication.seller.default = seller
    db.communication.id.readable = False
    db.communication.id.writable = False
    db.communication.buyer.writable = False
    db.communication.buyer.readable = False
    db.communication.seller.writable = False
    db.communication.item.writable = False
    form = SQLFORM(db.communication)
    if form.accepts(request, session):
        session.flash = 'Message sent!'
        redirect(URL('listing', args=item_id))
    elif form.errors:
        session.flash = 'Form has error!'
    return dict(form=form)


@auth.requires_login()
def editlisting():
    # display the item, if visitor is the seller of this item, then display a editable form
    item_id = request.args(0, cast=int) or redirect(URL('index'))
    item = db.item(item_id)
    itemname = item.item_name
    if item.created_by == auth.user_id:
        db.item.id.readable = False
        db.item.shop_name.readable = False
        db.item.shop_name.writable = False
        form = SQLFORM(db.item, item, deletable=True,
                       upload=URL('download'))
        form.add_button('Back', URL('index'))
        if form.process().accepted:
            session.flash = 'Item updated successful'
            redirect(URL('listing', args=item_id))
        elif form.errors:
            session.flash = 'Error in the form'
            redirect(URL('index'))
    else:
        redirect(URL('index'))

    return dict(form=form, name=itemname)


@auth.requires_login()
def editshop():
    # page for edit items for the shop, must be the owner of the shop
    shop_id = request.args(0, cast=int) or redirect(URL('index'))
    theshop = db.shop(shop_id)
    if auth.user_id != theshop.created_by:
        session.flash = 'the shop is not yours'
        redirect(URL('index'))
    elif auth.user_id == theshop.created_by:
        db.shop.id.readable = False
        db.shop.shop_owner.readable = False
        form = SQLFORM(db.shop, theshop, upload=URL('download'))
    return dict(form=form)


@auth.requires_login()
def cart():
    db.cart.id.readable = False
    db.cart.buyer.readable = False
    db.cart.item.writable = False
    db.cart.buyer.writable = False
    cart = db(db.cart.buyer == auth.user_id).select()
    if cart is None:
        session.flash = 'Your cart is empty'
        redirect(URL('index'))
    else:
        return dict(cart=SQLFORM.grid(db.cart.buyer == auth.user_id, create=False, csv=False, user_signature=False))


@auth.requires_login()
def openshop():
    user = db.auth_user(auth.user_id)
    if not user.is_seller:
        db.shop.shop_owner.readable = False
        form = SQLFORM(db.shop)
        if form.process().accepted:
            user.update_record(is_seller=True)
            redirect(URL('shop', args=auth.user_id))
    else:
        session.flash = 'You already have a shop!'
        redirect(URL('index'))
    return dict(form=form)


def shop():
    userid = request.args(0, cast=int) or redirect(URL('index'))
    shoptoshow = db(db.shop.shop_owner == userid).select().first()
    item_in_shop = db(db.item.shop_name == shoptoshow).select()
    return dict(shop=shoptoshow, items=item_in_shop)


def editalllisting():
    shopid = request.args(0, cast=int) or redirect(URL('index'))
    shoptoshow = db.shop(shopid)
    item_in_shop = db(db.item.shop_name == shopid)
    if item_in_shop.isempty():
        session.flash = "You don't have any listing yet, please add one"
        redirect(URL('newlisting'))
    return dict(shop=shoptoshow, items=item_in_shop)


@auth.requires_login()
def message():
    starter = db(db.auth_user.id == auth.user_id).select().first()
    if starter.is_seller:
        messages = db(db.communication.seller == starter)
        if messages.isempty():
            session.flash = 'You have no message yet'
            redirect(URL('index'))
            return
        messages = messages.select(orderby=~db.communication.created_on)
        db.communication.seller.default = starter.id
        db.communication.buyer.default = messages.first().buyer
        startSeller = True
    else:
        messages = db(db.communication.buyer == starter)
        if messages.isempty():
            session.flash = 'You have no message yet'
            redirect(URL('index'))
        messages = messages.select(orderby=~db.communication.created_on)
        db.communication.buyer.default = starter
        db.communication.seller.default = messages.first().seller
        startSeller = False
    db.communication.seller.writable = False
    db.communication.seller.readable = False
    db.communication.buyer.readable = False
    db.communication.buyer.writable = False
    form = SQLFORM(db.communication)
    form.add_button('Back', URL('index'))
    if form.process().accepted:
        session.flash = 'Message Sent!'
        redirect(URL('index'))
    return dict(messages=messages, form=form, start_is_seller=startSeller)


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
    http://..../[app]/default/user/bulk_register
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
