from datetime import datetime

from django.db import transaction
from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from course.models import Course, CourseExpire
from order.models import Order, OrderDetail


class OrderModelSerializer(ModelSerializer):
    class Meta:
        model = Order
        fields = ("id","order_number","pay_type")

        extra_kwargs = {
            "id":{"read_only":True},
            "order_number":{"read_only":True},
            "pay_type":{"write_only":True},
        }

    def validate(self, attrs):
        """对数据进行校验"""
        pay_type = attrs.get("pay_type")
        # print(pay_type,9999999)

        try:
            Order.pay_choices[pay_type]
        except Order.DoesNotExist:
            raise serializers.ValidationError("不支持您当前的支付方式~")

        return attrs

    def create(self, validated_data):
        """
        创建订单
        创建订单详情
        """
        # TODO 1.需要获取当前订单所需的数据
        redis_connection = get_redis_connection("cart")
        # print(1111111)
        # 获取当前登录的用户对象
        user_id = self.context['request'].user.id
        print(user_id)
        # user_id=2
        incr = redis_connection.incr("number")
        # print(user_id)

        # TODO 2.生成唯一的订单号 时间戳 用户ID 随机字符串
        order_number = datetime.now().strftime("%Y%m%d%H%M%S")+"%06d" % user_id + "%06d" % incr
        # print(order_number)
        with transaction.atomic():
            # 记录事务回滚的点
            savepoint = transaction.savepoint()
            # TODO 3.订单的生成
            order = Order.objects.create(
                order_title="百知教育在线商城订单",
                total_price=0,
                real_price=0,
                order_number=order_number,
                order_status=0,
                pay_type=validated_data.get("pay_type"),
                credit = 0,
                coupon = 0,
                order_desc="干得漂亮！！！",
                user_id = user_id,
            )
            # print(232323)
            cart_list = redis_connection.hgetall("cart_%s"%user_id)
            select_list = redis_connection.smembers("selected_%s"%user_id)
            # TODO 4.生成订单详情
            for course_id_byte,expire_id_byte in cart_list.items():
                course_id = int(course_id_byte)
                expire_id = int(expire_id_byte)
                # print(course_id,expire_id)

                # 判断商品是否被勾选
                if course_id_byte in select_list:
                    # 获取课程的所有信息
                    try:
                        course = Course.objects.get(is_show=True,is_delete=False,pk=course_id)
                    except:
                        raise serializers.ValidationError("对不起，您购买的商品不存在~")

                    # 如果课程有效期id大于0，则需要重新计算商品的价格，id不大于0则永久有效
                    origin_price = course.price
                    expire_text = "永久有效"

                    if expire_id>0:
                        course_expire = CourseExpire.objects.get(pk=expire_id)
                        # 获取有效期对应的原价
                        origin_price = course.price
                        expire_text = course_expire.expire_text

                    final_price = course.real_expire_price(expire_id)

                    try:
                        OrderDetail.objects.create(
                            order = order,
                            course = course,
                            expire=expire_id,
                            price=origin_price,
                            real_price=final_price,
                            discount_name=course.discount_name
                        )
                    except:
                        raise serializers.ValidationError("订单生成失败")
                    # 计算订单的总价 原价
                    order.total_price += float(origin_price)
                    order.real_price += float(final_price)
                    # TODO 5.如果已经成功生成了订单 需要将该商品从购物车中移除
                    redis_connection.hdel("cart_%s" % user_id, course_id)
                    redis_connection.srem("selected_%s" % user_id, course_id)

            order.save()
        # 遇到异常时  可以回滚到上个事务点
        transaction.savepoint_rollback(savepoint)
        return order

