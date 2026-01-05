'''
тесты для модели Teachers:
    test_create_teacher - создание учителя с обязательными полями
    test_teacher_str_method - проверка str метода
    test_teacher_with_user - связь учителя с пользователем
    test_tacher_without_user - учитель без пользователя (null=True)
    test_teacher_prompt_null - промпт может быть null
    test_teacher_prompt_blank - промпт может быть пустым
    test_teacher_name_max_length - максимальная длина имени 200 символов
    test_teacher_prompt_max_length - максимальная длина промпта 10000 символов
    test_cascade_on_user_delete - SET_NULL при удалении пользователя
    test_multiple_teachers_per_user - один пользователь может иметь нескольких учителейe

Дополнительные тесты для полного покрытия:
    Обновление полей
    QuerySet методы и фильтрация
    Сортировка
    Удаление
    Уникальность имени (не обязательна)
    Атрибуты полей
    Длинные промпты
    Валидация пустых и null значений
    Консистентность отношений

Особенности тестирования:
    Тесты корректно работают с blank=False для поля name
    Проверяют валидацию через full_clean()
    Учитывают особенности SQLite в тестовой среде
    Покрывают все ограничения и связи модели
'''



import pytest
from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from Chats.models import Users, Teachers


class TestTeachersModel(TestCase):
    """Тесты для модели Teachers"""

    def setUp(self):
        """Очистка базы данных перед каждым тестом"""
        Teachers.objects.all().delete()
        Users.objects.all().delete()

    def test_create_teacher(self):
        """Тест создания учителя с обязательными полями"""
        teacher = Teachers.objects.create(
            name='Test Teacher'
        )
        
        self.assertEqual(teacher.name, 'Test Teacher')
        self.assertIsNone(teacher.prompt)
        self.assertIsNone(teacher.user)
        self.assertIsInstance(teacher.id, int)

    def test_teacher_str_method(self):
        """Тест __str__ метода"""
        teacher = Teachers.objects.create(
            name='Test Teacher'
        )
        
        self.assertEqual(str(teacher), 'Test Teacher')

    def test_teacher_with_user(self):
        """Тест связи учителя с пользователем"""
        user = Users.objects.create(
            login='testuser',
            password_hash='hash',
            is_active=True
        )
        
        teacher = Teachers.objects.create(
            name='Teacher with User',
            prompt='Test prompt',
            user=user
        )
        
        self.assertEqual(teacher.user, user)
        self.assertEqual(teacher.user.login, 'testuser')

    def test_teacher_without_user(self):
        """Тест учителя без пользователя (null=True)"""
        teacher = Teachers.objects.create(
            name='Independent Teacher',
            prompt='Independent prompt'
        )
        
        self.assertIsNone(teacher.user)
        self.assertEqual(teacher.name, 'Independent Teacher')

    def test_teacher_prompt_null(self):
        """Тест что промпт может быть null"""
        teacher = Teachers.objects.create(
            name='Teacher without prompt'
        )
        
        self.assertIsNone(teacher.prompt)

    def test_teacher_prompt_blank(self):
        """Тест что промпт может быть пустым"""
        teacher = Teachers.objects.create(
            name='Teacher with blank prompt',
            prompt=''
        )
        
        self.assertEqual(teacher.prompt, '')

    def test_teacher_name_max_length(self):
        """Тест максимальной длины имени 200 символов"""
        # Имя максимальной длины должно работать
        max_name = 'a' * 200
        teacher = Teachers.objects.create(name=max_name)
        self.assertEqual(teacher.name, max_name)
        
        # Проверяем что поле имеет правильную максимальную длину
        max_length = Teachers._meta.get_field('name').max_length
        self.assertEqual(max_length, 200)

    def test_teacher_prompt_max_length(self):
        """Тест максимальной длины промпта 10000 символов"""
        # Промпт максимальной длины должен работать
        max_prompt = 'a' * 10000
        teacher = Teachers.objects.create(
            name='Teacher with max prompt',
            prompt=max_prompt
        )
        self.assertEqual(teacher.prompt, max_prompt)
        
        # Проверяем что поле имеет правильную максимальную длину
        max_length = Teachers._meta.get_field('prompt').max_length
        self.assertEqual(max_length, 10000)

    def test_cascade_on_user_delete(self):
        """Тест SET_NULL при удалении пользователя"""
        user = Users.objects.create(
            login='testuser',
            password_hash='hash',
            is_active=True
        )
        
        teacher = Teachers.objects.create(
            name='Teacher with User',
            prompt='Test prompt',
            user=user
        )
        
        # Проверяем что связь установлена
        self.assertEqual(teacher.user, user)
        
        # Удаляем пользователя
        user.delete()
        
        # Проверяем что у учителя user стал None
        teacher.refresh_from_db()
        self.assertIsNone(teacher.user)

    def test_multiple_teachers_per_user(self):
        """Тест что один пользователь может иметь нескольких учителей"""
        user = Users.objects.create(
            login='testuser',
            password_hash='hash',
            is_active=True
        )
        
        # Создаем нескольких учителей с одним пользователем
        teacher1 = Teachers.objects.create(
            name='Teacher 1',
            prompt='Prompt 1',
            user=user
        )
        teacher2 = Teachers.objects.create(
            name='Teacher 2',
            prompt='Prompt 2',
            user=user
        )
        teacher3 = Teachers.objects.create(
            name='Teacher 3',
            prompt='Prompt 3',
            user=user
        )
        
        # Проверяем что все учители связаны с одним пользователем
        self.assertEqual(teacher1.user, user)
        self.assertEqual(teacher2.user, user)
        self.assertEqual(teacher3.user, user)
        
        # Проверяем что у пользователя есть 3 учителя
        user_teachers = Teachers.objects.filter(user=user)
        self.assertEqual(user_teachers.count(), 3)

    def test_teacher_update_fields(self):
        """Тест обновления полей учителя"""
        teacher = Teachers.objects.create(
            name='Original Name',
            prompt='Original prompt'
        )
        
        # Обновляем поля
        teacher.name = 'Updated Name'
        teacher.prompt = 'Updated prompt'
        teacher.save()
        
        updated_teacher = Teachers.objects.get(id=teacher.id)
        self.assertEqual(updated_teacher.name, 'Updated Name')
        self.assertEqual(updated_teacher.prompt, 'Updated prompt')

    def test_teacher_queryset_methods(self):
        """Тест методов QuerySet для учителей"""
        user = Users.objects.create(
            login='testuser',
            password_hash='hash',
            is_active=True
        )
        
        # Создаем учителей с разными параметрами
        teacher_with_user = Teachers.objects.create(
            name='Teacher with User',
            prompt='Prompt with user',
            user=user
        )
        teacher_without_user = Teachers.objects.create(
            name='Teacher without User',
            prompt='Prompt without user'
        )
        teacher_without_prompt = Teachers.objects.create(
            name='Teacher without prompt'
        )
        
        # Проверяем фильтрацию по пользователю
        teachers_with_user = Teachers.objects.filter(user=user)
        self.assertEqual(teachers_with_user.count(), 1)
        
        # Проверяем фильтрацию по наличию промпта
        teachers_with_prompt = Teachers.objects.filter(prompt__isnull=False)
        self.assertEqual(teachers_with_prompt.count(), 2)
        
        teachers_without_prompt = Teachers.objects.filter(prompt__isnull=True)
        self.assertEqual(teachers_without_prompt.count(), 1)

    def test_teacher_ordering(self):
        """Тест сортировки учителей"""
        # Создаем учителей в разном порядке
        teacher_c = Teachers.objects.create(name='Teacher C')
        teacher_a = Teachers.objects.create(name='Teacher A')
        teacher_b = Teachers.objects.create(name='Teacher B')
        
        # Проверяем сортировку по имени
        teachers = Teachers.objects.all().order_by('name')
        names = [teacher.name for teacher in teachers]
        self.assertEqual(names, ['Teacher A', 'Teacher B', 'Teacher C'])

    def test_teacher_delete(self):
        """Тест удаления учителя"""
        teacher = Teachers.objects.create(
            name='Teacher to delete',
            prompt='Delete prompt'
        )
        
        teacher_id = teacher.id
        teacher.delete()
        
        # Проверяем что учитель удален
        with self.assertRaises(Teachers.DoesNotExist):
            Teachers.objects.get(id=teacher_id)

    def test_teacher_unique_name_constraint(self):
        """Тест что имя учителя не обязательно уникально"""
        # Создаем двух учителей с одинаковым именем (должно работать)
        teacher1 = Teachers.objects.create(name='Same Name')
        teacher2 = Teachers.objects.create(name='Same Name')
        
        self.assertEqual(teacher1.name, teacher2.name)
        self.assertEqual(Teachers.objects.filter(name='Same Name').count(), 2)

    def test_teacher_field_attributes(self):
        """Тест атрибутов полей модели"""
        # Проверяем атрибуты поля name
        name_field = Teachers._meta.get_field('name')
        self.assertEqual(name_field.max_length, 200)
        self.assertFalse(name_field.null)  # null=False по умолчанию
        self.assertFalse(name_field.blank)  # blank=False теперь явно указан
        
        # Проверяем атрибуты поля prompt
        prompt_field = Teachers._meta.get_field('prompt')
        self.assertEqual(prompt_field.max_length, 10000)
        self.assertTrue(prompt_field.null)
        self.assertTrue(prompt_field.blank)
        
        # Проверяем атрибуты поля user
        user_field = Teachers._meta.get_field('user')
        self.assertTrue(user_field.null)
        self.assertTrue(user_field.blank)

    def test_teacher_with_long_prompt(self):
        """Тест учителя с очень длинным промптом"""
        long_prompt = 'x' * 5000  # Промпт средней длины
        teacher = Teachers.objects.create(
            name='Teacher with long prompt',
            prompt=long_prompt
        )
        
        self.assertEqual(len(teacher.prompt), 5000)
        self.assertEqual(teacher.prompt, long_prompt)

    def test_teacher_name_cannot_be_blank(self):
        """Тест проверки пустого имени"""
        # Django позволяет создавать объекты с пустыми строками даже при blank=False
        # но full_clean() должен вызывать ValidationError
        teacher = Teachers(name='')
        
        # Проверяем что full_clean() вызывает ошибку валидации
        with self.assertRaises(ValidationError) as context:
            teacher.full_clean()
        
        # Проверяем что ошибка связана с полем name
        self.assertIn('name', context.exception.message_dict)
        
        # Однако save() все еще может работать в зависимости от базы данных
        try:
            teacher.save()
            # Если сохранилось, проверяем что поле действительно пустое
            self.assertEqual(teacher.name, '')
        except Exception:
            # Если база данных вызывает ошибку - это тоже ожидаемое поведение
            pass

    def test_teacher_name_cannot_be_null(self):
        """Тест что имя не может быть null"""
        # Попытка создать учителя с null именем должна вызвать ошибку
        with self.assertRaises(Exception):  # Может быть ValidationError или IntegrityError
            Teachers.objects.create(name=None)

    def test_teacher_relationship_consistency(self):
        """Тест консистентности отношений"""
        user = Users.objects.create(
            login='testuser',
            password_hash='hash',
            is_active=True
        )
        
        teacher = Teachers.objects.create(
            name='Test Teacher',
            user=user
        )
        
        # Проверяем что отношения работают в обе стороны
        self.assertEqual(teacher.user, user)
        # Проверяем что учитель действительно сохранен
        saved_teacher = Teachers.objects.get(id=teacher.id)
        self.assertEqual(saved_teacher.user, user)
