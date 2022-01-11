from django.core.paginator import Paginator


def paginator_for_posts(request, post_list, num_posts):
    """Paginator для вывода постов постранино."""
    paginator = Paginator(post_list, num_posts)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
