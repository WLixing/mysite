from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, render

from read_statistics.utils import read_statistics_once_read

from .models import Blog, BlogType


def page_info(request, blogs_all_list):
    paginator = Paginator(blogs_all_list, settings.EACH_PAGE_BLOGS_NUMBER)
    page_num = request.GET.get('page', 1)   # 获取URL页码参数(GET请求)
    page_of_blogs = paginator.get_page(page_num)  # 具体一页展示的信息
    currenter_page_num = page_of_blogs.number  # 获取当前页码
    # 获取当前页码前后两页的页码范围
    page_range = list(range(max(currenter_page_num - 2, 1), currenter_page_num)) + \
        list(range(currenter_page_num, min(
            currenter_page_num + 2, paginator.num_pages) + 1))
    # 加上页码省略标记
    if page_range[0] - 1 >= 2:
        page_range.insert(0, '...')
    if paginator.num_pages - page_range[-1] >= 2:
        page_range.append('...')
    # 加上首页和尾页
    if page_range[0] != 1:
        page_range.insert(0, 1)
    if page_range[-1] != paginator.num_pages:
        page_range.append(paginator.num_pages)

    # 获取博客分类对应类型的博客数量
    blog_types = BlogType.objects.all()
    blog_types_list = []
    for blog_type in blog_types:
        blog_type.blog_count = Blog.objects.filter(blog_type=blog_type).count()
        blog_types_list.append(blog_type)

    context = {}
    context['blogs'] = page_of_blogs.object_list
    context['page_of_blogs'] = page_of_blogs
    context['page_range'] = page_range
    context['blog_types'] = blog_types_list
    context['blog_dates'] = Blog.objects.dates(
        'created_time', 'month', order="DESC")

    return context


def blog_list(request):
    blogs_all_list = Blog.objects.all()
    context = page_info(request, blogs_all_list)
    return render(request, 'blog/blogs_list.html', context)


def blog_detail(request, blog_pk):
    blog = get_object_or_404(Blog, pk=blog_pk)
    read_cookie_key = read_statistics_once_read(request, blog)

    # blog_content_type = ContentType.objects.get_for_model(blog)
    # comments = Comment.objects.filter(
    #     content_type=blog_content_type, object_id=blog.pk, parent=None)

    context = {}
    context['previous_blog'] = Blog.objects.filter(
        created_time__gt=blog.created_time).last()
    context['next_blog'] = Blog.objects.filter(
        created_time__lt=blog.created_time).first()
    context['blog'] = blog

    # 下面代码转入了自定义模板
    # context['comments'] = comments.order_by('-comment_time')  # 让评论最新的先显示

    # context['comment_form'] = CommentForm(
    #     initial={'content_type': blog_content_type.model, 'object_id': blog_pk, 'reply_comment_id':'0'}) 
    response = render(request, 'blog/blog_detail.html', context)
    response.set_cookie(read_cookie_key, 'true')  # 阅读cookie标记 ,cookie的过期时间
    return response


def blogs_with_type(request, blog_type_pk):
    blog_type = get_object_or_404(BlogType, pk=blog_type_pk)
    blogs_all_list = Blog.objects.filter(blog_type=blog_type)
    context = page_info(request, blogs_all_list)
    context['blog_type'] = blog_type
    return render(request, 'blog/blogs_with_type.html', context)


def blogs_with_date(request, year, month):
    blogs_all_list = Blog.objects.filter(
        created_time__year=year, created_time__month=month)
    context = page_info(request, blogs_all_list)
    context['blogs_with_date'] = "%s年%s月" % (year, month)  # 传给模板页面的时间信息
    return render(request, 'blog/blogs_with_date.html', context)
