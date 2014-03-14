![http://i.imgur.com/voUSI65.png](http://i.imgur.com/voUSI65.png)
django-easy-split
=================

Easy split testing for Django.

## Features

* Simple installation and usage
* Statistical report generation
* Automatic bot exclusion

# Installation and Basic Usage

Getting started with **django-easy-split** is easy! Just install it, define your content to be tested and your goals, then sit back, wait for the data to roll in, then finally analyze and view your reports. You can do pretty much everything right from your templates, there's no need for you to ever creat your data models manually.

0. Install django-easy-split

    ```python
    pip install django-easy-split
    ```

1. Add 'easy_split' to your INSTALLED_APPS setting like this:

    ```python
    INSTALLED_APPS = (
      ...
      'easy_split',
    )
    ```

2. Sync your DB:

    ```python
    python manage.py syncdb
    ```

3. Add **easy_split** to your URLs:

    ```python
    urlpatterns = patterns('',

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/split/', include('easy_split.admin_urls')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^split/', include('easy_split.urls')),
    ```

4. Assign your visitors to experimental groups by wrapping your views with this decorator:

    ```python
    from easy_split.decorators import set_experiment_user

    @set_experiment_user
    return render_to_response('split_me.html', {
                                                  }, context_instance=RequestContext(request))
    ```

5. Include the necessary bot-excluding JavaScript in your base HTML. No jQuery is required!:

    ```html
    {% load split_js %}

    <head>
        {% split_js %}
    </head>

    ```

6. Define your test content:

    ```html
    {% load easy_split %}

    {% split try_or_buy control %}
    <a href="/payment/" class="btn btn-large btn-primary">
        Buy now!
    </a>
    {% endsplit %}

    {% split try_or_buy test %}
    <a href="/payment/" class="btn btn-large btn-primary">
        Try it free!
    </a>
    {% endsplit %}

    ```

7. Define your goals. The easiest way to do it is with an invisible pixel as shown here, or you can also do it programatically in your views.

    ```html
    <img src="/split/goal/try_or_buy" height="1" width="1" style="display: none" />
    ```

8. Test it out! Make sure that all of your URLs work and that GoalRecords are being created in your database.

9. Finally, once enough data has been collected over time, run:

    ```python
    python manage.py update_experiment_reports
    ```

    to generate your reports, then browse over to **/admin/split/** to see your reports!


## Origins

This project is a direct descendant of [django-lean](https://github.com/e-loue/django-lean/). For now, it's probably
best that you swim upstream for whatever you are looking for. This package also contains changes mentioned in [Alex
Kehayias's blog post](http://alexkehayias.tumblr.com/post/15951774761/ab-split-testing-django) on the subject.

django-easy-split intends to update and simplify django-lean. This may or may not ever actually come to fruition as a
useful product for the community - it may remain simply a mess of undocumented code only really useful for my own
purposes. Still, I'll be working in public for the most part, so we shall see.

## TODO

* Documentation, Packaging, Examples, Tests
* Email reporting?

