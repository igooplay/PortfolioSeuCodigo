import os
from flask import g, request
from app import app, db
from werkzeug.security import generate_password_hash
from models import User, Project, Service, Testimonial, SiteConfig

# Criar dados de exemplo se o banco estiver vazio
with app.app_context():
    # Verificar se existem usuários no banco
    if User.query.count() == 0:
        print("Criando dados de exemplo...")
        
        # Criar usuário admin
        admin = User(
            username="admin",
            email="admin@seucodigo.com.br",
            password_hash=generate_password_hash("admin123"),
            name="Administrador",
            bio="Administrador do sistema SeuCodigo.",
            is_admin=True
        )
        
        # Criar usuário normal
        user = User(
            username="cliente",
            email="cliente@exemplo.com",
            password_hash=generate_password_hash("cliente123"),
            name="Cliente Exemplo",
            bio="Cliente de exemplo para demonstração.",
            is_admin=False
        )
        
        db.session.add(admin)
        db.session.add(user)
        db.session.commit()
        
        # Criar projetos
        projects = [
            {
                "title": "E-commerce Responsivo",
                "description": "Desenvolvimento de uma plataforma completa de e-commerce com design responsivo, integração de pagamentos e painel administrativo personalizado.",
                "image_url": "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=800&q=80",
                "link": "https://exemplo.com/ecommerce"
            },
            {
                "title": "Aplicativo de Gestão Financeira",
                "description": "Aplicativo web para controle financeiro pessoal e empresarial, com gráficos em tempo real, exportação de relatórios e categorização automática de despesas.",
                "image_url": "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=800&q=80",
                "link": "https://exemplo.com/financas"
            },
            {
                "title": "Portal Institucional",
                "description": "Portal completo para empresa do setor imobiliário, com integração de busca de imóveis, formulários de contato e área de cliente.",
                "image_url": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=800&q=80",
                "link": "https://exemplo.com/portal"
            },
            {
                "title": "Sistema de Agendamento Online",
                "description": "Plataforma para agendamento de consultas médicas com integração de calendário, notificações por email e SMS, e painel administrativo.",
                "image_url": "https://images.unsplash.com/photo-1576091160550-2173dba999ef?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=800&q=80",
                "link": "https://exemplo.com/agenda"
            },
            {
                "title": "Marketplace de Cursos",
                "description": "Plataforma de venda e distribuição de cursos online com sistema de matrícula, área do aluno e certificação digital.",
                "image_url": "https://images.unsplash.com/photo-1501504905252-473c47e087f8?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=800&q=80",
                "link": "https://exemplo.com/cursos"
            }
        ]
        
        for project_data in projects:
            project = Project(**project_data)
            db.session.add(project)
        
        # Criar serviços
        services = [
            {
                "title": "Design Responsivo",
                "description": "Desenvolvimento de sites e aplicativos que se adaptam a qualquer dispositivo, garantindo a melhor experiência para seus usuários em smartphones, tablets e desktops.",
                "icon": "fas fa-mobile-alt",
                "price": 2500.00
            },
            {
                "title": "Desenvolvimento Web",
                "description": "Criação de websites e aplicações web modernas, otimizadas para SEO e com alta performance, utilizando as tecnologias mais avançadas do mercado.",
                "icon": "fas fa-code",
                "price": 4500.00
            },
            {
                "title": "E-commerce",
                "description": "Implementação de lojas virtuais completas com gestão de produtos, integração de pagamentos, controle de estoque e relatórios detalhados de vendas.",
                "icon": "fas fa-shopping-cart",
                "price": 6000.00
            },
            {
                "title": "Marketing Digital",
                "description": "Estratégias completas de marketing digital, incluindo SEO, gerenciamento de redes sociais, campanhas de anúncios e email marketing.",
                "icon": "fas fa-chart-line",
                "price": 1800.00
            },
            {
                "title": "Consultoria UX/UI",
                "description": "Análise e otimização da experiência do usuário e interface, com testes de usabilidade, prototipagem e redesign orientado a conversão.",
                "icon": "fas fa-paint-brush",
                "price": 3200.00
            },
            {
                "title": "Hospedagem e Suporte",
                "description": "Serviços de hospedagem gerenciada em servidores de alta performance, monitoramento 24/7, backups automáticos e suporte técnico especializado.",
                "icon": "fas fa-server",
                "price": 120.00
            }
        ]
        
        for service_data in services:
            service = Service(**service_data)
            db.session.add(service)
        
        # Criar depoimentos
        testimonials = [
            {
                "client_name": "Maria Silva",
                "content": "A equipe do SeuCodigo entregou nosso projeto antes do prazo e com qualidade excepcional. O processo foi transparente do início ao fim, e estamos extremamente satisfeitos com o resultado.",
                "company": "Silva & Associados",
                "position": "Diretora de Marketing",
                "rating": 5
            },
            {
                "client_name": "João Oliveira",
                "content": "Após tentativas frustradas com outras empresas, finalmente encontramos uma solução que realmente funciona! O sistema desenvolvido pelo SeuCodigo aumentou nossa produtividade em 40%.",
                "company": "Oliveira Tech",
                "position": "CEO",
                "rating": 5
            },
            {
                "client_name": "Ana Santos",
                "content": "O atendimento consultivo fez toda diferença no nosso projeto. Eles não apenas implementaram o que pedimos, mas sugeriram melhorias que nem tínhamos considerado.",
                "company": "Santos Imóveis",
                "position": "Gerente de Operações",
                "rating": 4
            },
            {
                "client_name": "Carlos Ferreira",
                "content": "Nosso e-commerce cresceu 300% após a implementação das melhorias sugeridas pela equipe. Especialmente as otimizações de SEO e performance que fizeram toda a diferença.",
                "company": "Ferreira Comércio",
                "position": "Proprietário",
                "rating": 5
            },
            {
                "client_name": "Luciana Mendes",
                "content": "A manutenção mensal tem sido essencial para manter nosso site sempre atualizado e seguro. O suporte é rápido e as atualizações são implementadas sem interromper nossos serviços.",
                "company": "Mendes Consultoria",
                "position": "Consultora Sênior",
                "rating": 4
            }
        ]
        
        for testimonial_data in testimonials:
            testimonial = Testimonial(**testimonial_data)
            db.session.add(testimonial)
        
        db.session.commit()
        print("Dados de exemplo criados com sucesso!")

if __name__ == '__main__':
    # Use socketio.run() com configurações mais compatíveis
    from app import socketio
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
