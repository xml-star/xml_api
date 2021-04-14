from django_redis import get_redis_connection
from rest_framework.generics import ListAPIView

# from home.contastnt import BANNER_LENGTH
from rest_framework.response import Response
from rest_framework.views import APIView

from home.models import Banner, Nav
from home.serializers import BannerModelSerializer, NavModelSerializer


class BannerListAPIView(ListAPIView):
    queryset = Banner.objects.filter(is_show=True, is_delete=False).order_by("orders")
    serializer_class = BannerModelSerializer

class HeaderListAPIView(ListAPIView):
    queryset = Nav.objects.filter(is_show=True, is_delete=False,position=1).order_by("orders")
    # print(queryset)

    serializer_class = NavModelSerializer
class GetCartLength(APIView):
    def get(self,request,*args,**kwargs):
        user_id = request.user.id
        # 建立连接
        redis_connection = get_redis_connection("cart")
        # 获取购物车中商品的总数据量
        course_len = redis_connection.hlen("cart_%s" % user_id)
        # print(course_len)
        return Response({"message": "成功", "cart_length": course_len})


class BottomListAPIView(ListAPIView):
    queryset = Nav.objects.filter(is_show=True, is_delete=False,position=2).order_by("orders")
    serializer_class = NavModelSerializer