{
    'name': 'Certificación SII Chile',
    'version': '1.0',
    'category': 'Accounting/Localization/Chile',
    'summary': 'Herramientas para facilitar el proceso de certificación con el SII en Chile',
    'description': """
    Módulo para facilitar el proceso de certificación con el SII en Chile
    ====================================================================

    Este módulo proporciona herramientas que facilitan el proceso de certificación 
    con el Servicio de Impuestos Internos (SII) de Chile para la facturación electrónica.

    Funcionalidades:
    ---------------
    * Panel de control para el proceso de certificación
    * Preparación automática de la base de datos
    * Creación de CAFs de demostración
    * Procesamiento de set de pruebas (simulado con datos demo)
    * Seguimiento de documentos de prueba
    """,
    'author': 'Tomás Díaz',
    'website': 'https://www.withinplaygames.com',
    'depends': ['account', 'l10n_cl', 'l10n_cl_edi', 'l10n_cl_edi_stock', 'l10n_cl_edi_exports'],
    'external_dependencies': {
        'python': ['lxml'],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/certification_process_view.xml',
        'views/certification_batch_file_views.xml',
        'views/test_set_views.xml',
        'views/report_invoice_fix.xml',
        'views/certification_iecv_book_view.xml',
        'views/certification_delivery_guide_book_view.xml',
        'views/dte_template_certification.xml',  # Template para referencias SET
        'views/stock_picking_certification_views.xml',  # Vista extendida para stock.picking
        'wizard/certification_reset_wizard_view.xml',
        'wizard/iecv_generator_wizard_view.xml',
        'data/l10n_cl_edi_certification_data.xml',
        'data/certification_partners.xml',
        'data/certification_export_partners.xml',
        'data/certification_purchase_partners.xml',
        'data/certification_export_products.xml',
        'data/certification_currencies.xml',
        'data/l10n_cl_edi_certification_basic_set_05.xml',
        'data/l10n_cl_edi_certification_purchase_book_05.xml',
        'data/l10n_cl_edi_certification_delivery_guides_05.xml',
        'data/l10n_cl_edi_certification_export_documents_05.xml',
        'data/l10n_cl_edi_certification_purchase_invoice_05.xml',
    ],
    'uninstall_hook': 'uninstall_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}