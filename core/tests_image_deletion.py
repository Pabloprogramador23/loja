import os
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage
from django.contrib.auth.models import User
from .models import Store, Product, Category
from .forms import StoreSettingsForm, ProductForm


class ImageDeletionTestCase(TestCase):
    def setUp(self):
        # Create a test owner
        self.owner = User.objects.create_user(
            username='testowner',
            email='testowner@example.com',
            password='password123'
        )
        
        # Create a test store (tenant)
        self.store = Store.objects.create(
            name='Test Store',
            subdomain='teststore',
            owner=self.owner
        )
        
        # Create a test category
        self.category = Category.objects.create(
            name='Test Category',
            store=self.store
        )

        # Create mock images (1x1 transparent GIF)
        gif_data = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01D\x00;'
        self.logo_file = SimpleUploadedFile(
            name='test_logo.png',
            content=gif_data,
            content_type='image/png'
        )
        self.cover_file = SimpleUploadedFile(
            name='test_cover.png',
            content=gif_data,
            content_type='image/png'
        )
        self.product_file = SimpleUploadedFile(
            name='test_product.png',
            content=gif_data,
            content_type='image/png'
        )

    def test_store_settings_form_clears_and_deletes_files(self):
        # 1. First, save logo and cover_image
        form_data = {
            'name': 'Updated Store Name',
            'mercadopago_access_token': 'TEST-123456',
            'delivery_fee': '5.00',
            'delivery_enabled': True,
            'payment_online_enabled': True,
            'payment_cash_enabled': True,
            'payment_card_enabled': True,
        }
        file_data = {
            'logo': self.logo_file,
            'cover_image': self.cover_file
        }
        
        form = StoreSettingsForm(form_data, file_data, instance=self.store)
        self.assertTrue(form.is_valid())
        store = form.save()
        
        logo_path = store.logo.path
        cover_path = store.cover_image.path
        
        # Verify files exist on disk
        self.assertTrue(os.path.exists(logo_path))
        self.assertTrue(os.path.exists(cover_path))
        
        # 2. Submit form to clear logo and cover image
        clear_form_data = form_data.copy()
        clear_form_data['clear_logo'] = True
        clear_form_data['clear_cover_image'] = True
        
        form = StoreSettingsForm(clear_form_data, instance=self.store)
        self.assertTrue(form.is_valid())
        store = form.save()
        
        # Verify db fields are None
        self.assertIsNone(store.logo.name)
        self.assertIsNone(store.cover_image.name)
        
        # Verify physical files are deleted
        self.assertFalse(os.path.exists(logo_path))
        self.assertFalse(os.path.exists(cover_path))

    def test_product_form_clears_and_deletes_file(self):
        # 1. Create product with image
        product = Product.objects.create(
            name='Test Product',
            price='10.00',
            category=self.category,
            store=self.store,
            image=self.product_file
        )
        
        product_image_path = product.image.path
        self.assertTrue(os.path.exists(product_image_path))
        
        # 2. Submit ProductForm with clear_image = True
        form_data = {
            'name': 'Test Product Updated',
            'price': '12.00',
            'category': self.category.id,
            'is_available': True,
            'clear_image': True,
        }
        
        form = ProductForm(form_data, instance=product)
        self.assertTrue(form.is_valid())
        product = form.save()
        
        # Verify db field is None
        self.assertIsNone(product.image.name)
        
        # Verify physical file is deleted
        self.assertFalse(os.path.exists(product_image_path))
