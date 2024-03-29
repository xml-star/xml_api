from django.db import models

# Create your models here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import IsAuthenticated
from django_redis import get_redis_connection

from course.models import Course, CourseExpire
from xml_api.utils import contastnt


class CartViewSet(ViewSet):
    """购物车相关操作"""

    # 只有登录成功的用户才可以访问此接口
    permission_classes = [IsAuthenticated]

    def add_cart(self, request):
        """
        将用户在前端提交的信息保存至购物车
        params: 用户id  课程id  勾选状态  有效期
        """
        course_id = request.data.get("course_id")

        user_id = request.user.id
        print(user_id)
        # 是否勾选
        select = True
        # 有效期
        expire = 0

        # 校验前端参数
        try:
            Course.objects.get(is_show=True, is_delete=False, pk=course_id)
        except Course.DoesNotExist:
            return Response({"message": "参数有误，课程不存在"},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            # 获取数据库连接
            redis_connection = get_redis_connection("cart")

            # 将数据保存到redis  使用redis管道
            pipeline = redis_connection.pipeline()
            # 保存的是商品的信息以及对应的有效期
            pipeline.hset("cart_%s" % user_id, course_id, expire)
            # 商品的勾选状态
            pipeline.sadd("selected_%s" % user_id, course_id)

            # 执行命令
            pipeline.execute()

            # 获取购物车中商品的总数据量
            course_len = redis_connection.hlen("cart_%s" % user_id)

        except:
            return Response({"message": "参数有误，购物车添加失败"},
                            status=status.HTTP_507_INSUFFICIENT_STORAGE)

        return Response({"message": "购物车添加成功", "cart_length": course_len})

    def list_cart(self, request):
        """展示购物车"""

        # 获取所需参数
        user_id = request.user.id
        # user_id = 1
        redis_connection = get_redis_connection("cart")
        cart_list_bytes = redis_connection.hgetall("cart_%s" % user_id)
        selected_list_bytes = redis_connection.smembers("selected_%s" % user_id)

        # 获取前端所需的商品信息

        total_price = 0
        data = []
        for course_id_byte, expire_id_byte in cart_list_bytes.items():
            course_id = int(course_id_byte)
            expire_id = int(expire_id_byte)
            try:
                # 循环找到所有需要的课程信息
                course = Course.objects.get(is_show=True, pk=course_id, is_delete=False)
            except Course.DoesNotExist:
                continue

                # 将前端所需的信息返回
            data.append({
                "selected": True if course_id_byte in selected_list_bytes else False,
                "course_img": contastnt.IMG_SRC + course.course_img.url,
                "name": course.name,
                "price": course.real_expire_price(expire_id),
                "id": course.id,
                "expire_list":course.expire_list,
                "expire_id":expire_id,
            })

        return Response({"cart_list":data})

    # 定义视图，删除购物车中的商品
    def del_course(self, request):
        # 获取所需参数
        # user_id = 1
        user_id = request.user.id
        course_id = request.query_params.get("course_id")
        # 建立连接
        redis_connection = get_redis_connection("cart")

        try:

            # 在购物车中删除该项
            redis_connection.hdel("cart_%s" % user_id, course_id)
            # 在选择集合中删除该项
            redis_connection.srem("selected_%s" % user_id, course_id)

            # 获取购物车中商品的总数据量
            course_len = redis_connection.hlen("cart_%s" % user_id)
            print(course_len)
        except:
            return Response({
                "message": "删除失败!!",
            }, status=status.HTTP_507_INSUFFICIENT_STORAGE)
        # return Response({"message": "购物车添加成功", "cart_length": course_len})

        return Response({
            "message": "删除成功!!",
            "cart_length": course_len
        }, status=status.HTTP_200_OK,)

    # 定义部分修改购物车中商品的属性
    def change_select(self, request):
        # 获取所需参数
        user_id = request.user.id
        # user_id = 1
        # print(user_id)
        course_id = request.data.get("course_id")
        flag = request.data.get("selected")
        # print(user_id,course_id)

        # 建立连接
        redis_connection = get_redis_connection("cart")
        try:
            if not flag:
                # 在选择集合中删除该项
                redis_connection.srem("selected_%s" % user_id, course_id)
            else:
                # 在选择集合中加入该项
                redis_connection.sadd("selected_%s" % user_id, course_id)
        except:
            return Response({
                "message": "更新失败!!",
            }, status=status.HTTP_507_INSUFFICIENT_STORAGE)

        return Response({
            "message": "更新成功!!",
        }, status=status.HTTP_200_OK)

    # 修改有效期
    def change_expire(self, request):
        """改变redis中课程有效期"""
        # 获取用户id  课程id  有效期id
        user_id = request.user.id
        expire_id = request.data.get("expire_id")
        course_id = request.data.get("course_id")
        # print(user_id,expire_id,course_id)
        price = 0
        # 查询操作的课程是否存在
        try:
            course = Course.objects.get(is_delete=False, is_show=True, pk=course_id)
            price = course.real_expire_price(expire_id)
            # 如果前端传递的有效期的id不是0 则修改对应课程的有效期
            if expire_id > 0:
                expire_obj = CourseExpire.objects.filter(is_show=True, is_delete=False, pk=expire_id)
                if not expire_obj:
                    raise CourseExpire.DoesNotExist("课程有效期不存在")

        except Course.DoesNotExist:
            return Response({"message": "课程信息不存在"}, status=status.HTTP_400_BAD_REQUEST)

        redis_connection = get_redis_connection("cart")
        redis_connection.hset("cart_%s" % user_id, course_id, expire_id)
        # print(expire_id,price)

        return Response({"message": "有效期切换成功","expire_price":price})

    # 获取购物车中选中的课程 渲染订单页面
    def get_select_course(self,request):
        user_id = request.user.id
        # user_id = 1
        # 连接redis数据库
        redis_connection = get_redis_connection("cart")

        # 获取当前登录用户的购物车数据
        cart_list = redis_connection.hgetall("cart_%s" % user_id)
        select_list = redis_connection.smembers("selected_%s" % user_id)

        # 商品总价
        total_price = 0
        data = []

        for course_id_byte,expire_id_byte in cart_list.items():
            course_id = int(course_id_byte)
            expire_id = int(expire_id_byte)

            # 判断商品是否被勾选
            if course_id_byte in select_list:
                # 获取课程的所有信息
                try:
                    course = Course.objects.get(is_show=True,is_delete=False,pk = course_id)
                except Course.DoesNotExist:
                    continue

                # TODO 计算商品的总价格
                # 如果课程的有效期id大于0，则需要重新计算商品的价格，id不大于0则是永久有效
                origin_price = course.price
                expire_text = "永久有效"

                if expire_id>0:
                    course_expire = CourseExpire.objects.get(pk=expire_id)
                    expire_text = course_expire.expire_text

                final_price = course.real_expire_price(expire_id)

                # 将订单结算页所需的数据返回
                data.append({
                    "course_img":contastnt.IMG_SRC+course.course_img.url,
                    "name":course.name,
                    "final_price":course.real_expire_price(expire_id),
                    "id":course.id,
                    "expire_text":expire_text,
                    "price":"%.2f" % origin_price,
                })

                # 商品的总价
                total_price += float(final_price)
        return Response({"course_list":data,"total_price":"%.2f"%total_price,"message":"获取成功"})





