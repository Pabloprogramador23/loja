from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Store, Category, Product, Order, OrderItem
from core.utils import set_current_tenant, reset_current_tenant
from decimal import Decimal

class Command(BaseCommand):
    help = 'Seeds the database with realistic initial data'

    def handle(self, *args, **options):
        self.stdout.write("Checking for existing data...")
        
        # Ensure we have a tenant
        store, created = Store.objects.get_or_create(
            subdomain='loja1',
            defaults={'name': 'Loja 1 - Matrix', 'is_active': True}
        )
        set_current_tenant(store)

        if created:
             self.stdout.write(f"Store '{store.name}' created.")
        else:
             self.stdout.write(f"Store '{store.name}' found.")

        # Create Superuser if not exists
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin')
            self.stdout.write("Superuser 'admin' created.")

        # Create Customers
        user1, _ = User.objects.get_or_create(username='cliente1', defaults={'email': 'c1@test.com'})
        if _: user1.set_password('123456'); user1.save()
        
        user2, _ = User.objects.get_or_create(username='cliente2', defaults={'email': 'c2@test.com'})
        if _: user2.set_password('123456'); user2.save()

        self.stdout.write("Seeding menu data...")

        menu = {
            "Hambúrgueres Artesanais": [
                ("X-Bacon Crocante", 28.90, "Pão brioche, blend 180g, bacon crocante, queijo cheddar e maionese da casa."),
                ("X-Salada Clássico", 24.50, "Pão com gergelim, blend 150g, alface, tomate, queijo prato e molho especial."),
                ("Smash Duplo", 32.00, "Dois smash burgers de 80g, queijo cheddar duplo, cebola picada e mostarda."),
                ("O Monstruoso", 45.00, "Três carnes, ovo, bacon, cheddar, onion rings e barbecue."),
                ("Veggie Burger", 29.90, "Hambúrguer de grão de bico, alface, tomate, cebola roxa e maionese vegana."),
            ],
            "Pizzas Brotinho": [
                ("Calabresa Acebolada", 22.00, "Molho de tomate, mussarela, calabresa fatiada e cebola."),
                ("Marguerita", 20.00, "Molho, mussarela, tomate e manjericão fresco."),
                ("Frango com Catupiry", 24.50, "Frango desfiado temperado coberto com legítimo catupiry."),
                ("Quatro Queijos", 25.00, "Mussarela, provolone, parmesão e gorgonzola."),
                ("Portuguesa", 23.00, "Presunto, palmito, ovo, ervilha e cebola."),
            ],
            "Pastéis de Feira": [
                ("Carne com Azeitona", 8.50, "Pastel sequinho de carne moída temperada com azeitonas."),
                ("Queijo", 7.50, "Muito queijo mussarela derretido."),
                ("Pizza", 8.00, "Queijo, presunto e orégano."),
                ("Frango com Requeijão", 9.00, "Recheio cremoso de frango."),
                ("Palmito Especial", 10.00, "Palmito picado com molho branco."),
            ],
            "Bebidas": [
                ("Coca-Cola Lata 350ml", 6.00, "Bem gelada."),
                ("Guaraná Antarctica 350ml", 6.00, "O original."),
                ("Suco de Laranja Natural", 12.00, "500ml, feito na hora."),
                ("Água Mineral", 4.00, "Sem gás 500ml."),
                ("Cerveja Long Neck", 14.00, "Heineken ou Stella."),
            ],
            "Sobremesas": [
                ("Pudim de Leite", 12.00, "Fatia generosa de pudim liso e cremoso."),
                ("Brownie com Sorvete", 18.00, "Brownie quente com bola de sorvete de creme."),
                ("Milkshake de Nutella", 22.00, "500ml de pura cremosidade."),
            ]
        }

        for cat_name, items in menu.items():
            category, _ = Category.objects.get_or_create(name=cat_name)
            for prod_name, price, desc in items:
                Product.objects.get_or_create(
                    name=prod_name,
                    category=category,
                    defaults={
                        'price': Decimal(str(price)),
                        'description': desc,
                        'is_available': True
                    }
                )

        self.stdout.write(self.style.SUCCESS('Successfully seeded realistic menu data!'))
