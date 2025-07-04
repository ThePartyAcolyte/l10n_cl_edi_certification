# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class CertificationCaseDte(models.Model):
    _name = 'l10n_cl_edi.certification.case.dte'
    _description = 'Caso DTE de Certificación'
    _rec_name = 'case_number_display'

    # Campos básicos
    case_number_raw = fields.Char(string='Número de Caso (Raw)', required=True)
    case_number_display = fields.Char(string='Número de Caso', compute='_compute_case_number_display', store=True)
    document_type_code = fields.Char(string='Código Tipo Documento', required=True)
    document_type_name = fields.Char(string='Nombre Tipo Documento', compute='_compute_document_type_name', store=True)
    document_type_raw = fields.Char(string='Tipo Documento (Raw)')
    
    # Relaciones
    parsed_set_id = fields.Many2one(
        'l10n_cl_edi.certification.parsed_set',
        string='Set de Pruebas',
        required=True,
        ondelete='cascade'
    )
    partner_id = fields.Many2one(
        'res.partner', 
        string='Cliente',
        help='Partner asignado durante la generación del documento'
    )
    
    # Estado de generación
    generation_status = fields.Selection([
        ('pending', 'Pendiente'),
        ('generated', 'Generado'),
        ('error', 'Error')
    ], string='Estado Generación', default='pending', track_visibility='onchange')
    
    # Documentos generados
    generated_account_move_id = fields.Many2one(
        'account.move',
        string='Factura Generada',
        readonly=True,
        help='Factura generada desde este caso DTE'
    )
    generated_batch_account_move_id = fields.Many2one(
        'account.move',
        string='Factura Batch Generada',
        readonly=True,
        help='Factura regenerada para proceso de envío consolidado con nuevos folios CAF'
    )
    generated_stock_picking_id = fields.Many2one(
        'stock.picking',
        string='Guía de Despacho Generada',
        readonly=True,
        help='Guía de despacho generada desde este caso DTE'
    )
    generated_batch_stock_picking_id = fields.Many2one(
        'stock.picking',
        string='Guía de Despacho Batch Generada',
        readonly=True,
        help='Guía de despacho regenerada para proceso de envío consolidado con nuevos folios CAF'
    )
    
    # Relaciones con items y referencias
    item_ids = fields.One2many(
        'l10n_cl_edi.certification.case.dte.item', 'case_dte_id',
        string='Ítems del Documento')
    reference_ids = fields.One2many(
        'l10n_cl_edi.certification.case.dte.reference', 'case_dte_id',
        string='Referencias del Documento')
    
    # Campos adicionales
    error_message = fields.Text(string='Mensaje de Error')
    notes = fields.Text(string='Notas')
    
    # Campos computados
    # Campo computado para mostrar estado completo
    # Campo computado para mostrar información de la factura
    
    # Campos adicionales para diferentes tipos de documentos
    global_discount_percent = fields.Float(string='Descuento Global (%)')
    
    # Guía de Despacho específicos
    dispatch_motive_raw = fields.Text(string='Motivo Traslado (Raw)')
    dispatch_transport_type_raw = fields.Text(string='Tipo de Traslado (Raw)')
    
    # Documentos de Exportación específicos
    export_reference_text = fields.Text(string='Texto Referencia Exportación')
    export_currency_raw = fields.Char(string='Moneda Operación (Raw)')
    export_payment_terms_raw = fields.Char(string='Forma de Pago Exportación (Raw)')
    export_sale_modality_raw = fields.Text(string='Modalidad de Venta (Raw)')
    export_sale_clause_raw = fields.Char(string='Cláusula de Venta (Raw)')
    export_total_sale_clause_amount = fields.Float(string='Total Cláusula Venta')
    export_transport_way_raw = fields.Char(string='Vía de Transporte (Raw)')
    export_loading_port_raw = fields.Char(string='Puerto Embarque (Raw)')
    export_unloading_port_raw = fields.Char(string='Puerto Desembarque (Raw)')
    export_tare_uom_raw = fields.Char(string='Unidad Medida Tara (Raw)')
    export_gross_weight_uom_raw = fields.Char(string='Unidad Peso Bruto (Raw)')
    export_net_weight_uom_raw = fields.Char(string='Unidad Peso Neto (Raw)')
    export_package_type_raw = fields.Char(string='Tipo de Bulto (Raw)')
    export_total_packages = fields.Integer(string='Total Bultos')
    export_recipient_country_raw = fields.Char(string='País Receptor (Raw)')
    export_destination_country_raw = fields.Char(string='País Destino (Raw)')
    export_freight_amount = fields.Float(string='Monto Flete', digits=(18, 4), help='MntFlete: Monto del flete con 4 decimales')
    export_insurance_amount = fields.Float(string='Monto Seguro', digits=(18, 4), help='MntSeguro: Monto del seguro con 4 decimales')
    export_client_nationality_raw = fields.Char(string='Nacionalidad Cliente (Raw)')
    export_foreign_commission_percent = fields.Float(string='% Comisiones Extranjero')
    
    # Texto original
    raw_text_block = fields.Text(string='Bloque de Texto Original del Caso')
    
    @api.depends('case_number_raw')
    def _compute_case_number_display(self):
        for record in self:
            if record.case_number_raw:
                record.case_number_display = f"Caso {record.case_number_raw}"
            else:
                record.case_number_display = "Sin número"

    @api.depends('document_type_code')
    def _compute_document_type_name(self):
        for record in self:
            if record.document_type_code:
                # Buscar el tipo de documento en Odoo
                doc_type = self.env['l10n_latam.document.type'].search([
                    ('code', '=', record.document_type_code),
                    ('country_id.code', '=', 'CL')
                ], limit=1)
                
                if doc_type:
                    record.document_type_name = doc_type.name
                else:
                    record.document_type_name = f"Tipo {record.document_type_code}"
            else:
                record.document_type_name = "Sin tipo"


    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        """
        Override search_read to automatically sync DTE case statuses when loading data.
        """
        # Ejecutar búsqueda estándar
        result = super().search_read(domain, fields, offset, limit, order)
        
        # Sincronizar estados automáticamente
        try:
            # Obtener IDs de los registros cargados
            record_ids = [r['id'] for r in result if 'id' in r]
            if record_ids:
                records = self.browse(record_ids)
                records._sync_generation_status()
        except Exception as e:
            _logger.warning(f"Error sincronizando estados DTE: {str(e)}")
        
        return result

    def _sync_generation_status(self):
        """
        Sincroniza el estado de generación de los casos DTE con los documentos existentes.
        """
        for record in self:
            try:
                # Verificar si hay factura vinculada
                if record.generated_account_move_id:
                    # Si hay factura vinculada, verificar que exista y esté activa
                    if record.generated_account_move_id.exists() and record.generated_account_move_id.state != 'cancel':
                        # Factura existe y está activa
                        if record.generation_status != 'generated':
                            record.generation_status = 'generated'
                            _logger.info(f"Sincronizado caso {record.id}: estado → 'generated'")
                    else:
                        # Factura no existe o está cancelada, desvincular
                        record.generated_account_move_id = False
                        record.generation_status = 'pending'
                        _logger.info(f"Sincronizado caso {record.id}: factura inexistente, estado → 'pending'")
                
                # Verificar si hay guía de despacho vinculada
                elif record.generated_stock_picking_id:
                    # Si hay guía vinculada, verificar que exista y esté activa
                    if record.generated_stock_picking_id.exists() and record.generated_stock_picking_id.state != 'cancel':
                        # Guía existe y está activa
                        if record.generation_status != 'generated':
                            record.generation_status = 'generated'
                            _logger.info(f"Sincronizado caso {record.id}: estado → 'generated' (guía)")
                    else:
                        # Guía no existe o está cancelada, desvincular
                        record.generated_stock_picking_id = False
                        record.generation_status = 'pending'
                        _logger.info(f"Sincronizado caso {record.id}: guía inexistente, estado → 'pending'")
                
                else:
                    # No hay documento vinculado, buscar si existe un documento relacionado
                    potential_invoice = self.env['account.move'].search([
                        ('ref', '=', f'Certificación DTE - Caso {record.id}'),
                        ('state', '!=', 'cancel')
                    ], limit=1)
                    
                    # Buscar guía de despacho relacionada (por referencia al caso)
                    potential_picking = self.env['stock.picking'].search([
                        ('origin', 'ilike', f'Caso {record.id}'),
                        ('state', '!=', 'cancel')
                    ], limit=1)
                    
                    if potential_invoice:
                        # Encontrada factura relacionada, vincular
                        record.generated_account_move_id = potential_invoice
                        record.generation_status = 'generated'
                        _logger.info(f"Sincronizado caso {record.id}: factura encontrada {potential_invoice.name}, estado → 'generated'")
                    elif potential_picking:
                        # Encontrada guía relacionada, vincular
                        record.generated_stock_picking_id = potential_picking
                        record.generation_status = 'generated'
                        _logger.info(f"Sincronizado caso {record.id}: guía encontrada {potential_picking.name}, estado → 'generated'")
                    else:
                        # No hay documento relacionado
                        if record.generation_status == 'generated':
                            record.generation_status = 'pending'
                            _logger.info(f"Sincronizado caso {record.id}: sin documento, estado → 'pending'")
            except Exception as e:
                _logger.warning(f"Error sincronizando caso {record.id}: {str(e)}")

    def action_reset_case(self):
        """
        Resetea el caso DTE para permitir regeneración.
        Maneja la desvinculación de documentos existentes (facturas o guías).
        """
        self.ensure_one()
        
        # Manejar factura vinculada
        if self.generated_account_move_id:
            invoice = self.generated_account_move_id
            
            if invoice.state == 'draft':
                # Si la factura está en borrador, preguntar qué hacer
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Confirmar Reset',
                    'res_model': 'l10n_cl_edi.certification.reset.wizard',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {
                        'default_case_id': self.id,
                        'default_invoice_id': invoice.id,
                        'default_invoice_name': invoice.name,
                        'default_invoice_state': invoice.state,
                    }
                }
            elif invoice.state in ['posted', 'cancel']:
                # Si la factura está validada o cancelada, solo desvincular
                self.generated_account_move_id = False
                self.generation_status = 'pending'
                _logger.info(f"Caso {self.id} reseteado. Factura {invoice.name} desvinculada (estado: {invoice.state})")
            else:
                raise UserError(f"No se puede resetear: la factura {invoice.name} está en estado {invoice.state}")
        
        # Manejar guía de despacho vinculada
        elif self.generated_stock_picking_id:
            picking = self.generated_stock_picking_id
            
            if picking.state in ['draft', 'waiting', 'confirmed', 'assigned']:
                # Si la guía está en estados previos a done, solo desvincular
                self.generated_stock_picking_id = False
                self.generation_status = 'pending'
                _logger.info(f"Caso {self.id} reseteado. Guía {picking.name} desvinculada (estado: {picking.state})")
            elif picking.state in ['done', 'cancel']:
                # Si la guía está validada o cancelada, solo desvincular
                self.generated_stock_picking_id = False
                self.generation_status = 'pending'
                _logger.info(f"Caso {self.id} reseteado. Guía {picking.name} desvinculada (estado: {picking.state})")
            else:
                raise UserError(f"No se puede resetear: la guía {picking.name} está en estado {picking.state}")
        
        else:
            # Si no hay documento vinculado, simplemente resetear estado
            self.generation_status = 'pending'
            _logger.info(f"Caso {self.id} reseteado a estado 'pending'")
        
        return True

    def action_view_document(self):
        """Abrir el documento vinculado (factura o guía de despacho)"""
        self.ensure_one()
        
        if self.generated_account_move_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Factura Vinculada',
                'res_model': 'account.move',
                'res_id': self.generated_account_move_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        elif self.generated_stock_picking_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Guía de Despacho Vinculada',
                'res_model': 'stock.picking',
                'res_id': self.generated_stock_picking_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            raise UserError("Este caso DTE no tiene un documento vinculado")
    
    def action_view_invoice(self):
        """Mantener compatibilidad - redirige a action_view_document"""
        return self.action_view_document()

    def action_generate_document(self):
        """Generar documento desde el caso DTE"""
        self.ensure_one()
        
        # **DIAGNÓSTICO PREVIO**
        _logger.info(f"\n=== DIAGNÓSTICO CASO DTE {self.id} ===")
        _logger.info(f"Número: {self.case_number_raw}")
        _logger.info(f"Tipo documento: '{self.document_type_code}' ({self.document_type_name})")
        _logger.info(f"Estado: {self.generation_status}")
        _logger.info(f"Referencias: {len(self.reference_ids)}")
        
        for i, ref in enumerate(self.reference_ids, 1):
            _logger.info(f"  Ref {i}: {ref.reference_document_text_raw} -> {ref.referenced_sii_case_number}")
            _logger.info(f"    Código: '{ref.reference_code}', Razón: '{ref.reason_raw}'")
            if ref.referenced_case_dte_id:
                _logger.info(f"    Caso referenciado: {ref.referenced_case_dte_id.case_number_raw} (tipo: {ref.referenced_case_dte_id.document_type_code})")
            else:
                _logger.info(f"    Caso referenciado: NO VINCULADO")
        
        _logger.info(f"Ítems: {len(self.item_ids)}")
        for i, item in enumerate(self.item_ids, 1):
            _logger.info(f"  Item {i}: {item.name} - Cant: {item.quantity}, Precio: {item.price_unit}")
        
        _logger.info(f"=== FIN DIAGNÓSTICO ===\n")
        
        # Crear el generador y ejecutar
        generator = self.env['l10n_cl_edi.certification.document.generator'].create({
            'dte_case_id': self.id,
            'certification_process_id': self.parsed_set_id.certification_process_id.id,
        })
        
        return generator.generate_document() 

    # Métodos computados eliminados - ya no se usan en la vista simplificada 