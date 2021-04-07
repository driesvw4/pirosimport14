odoo.define('piros.source_document_link', function(require) {
    "use strict";

    var core = require('web.core');
    var BasicFields= require('web.basic_fields');
    var FormController = require('web.FormController');
    var Registry = require('web.field_registry');
    var utils = require('web.utils');
    var session = require('web.session');
    var field_utils = require('web.field_utils');

    var _t = core._t;
    var QWeb = core.qweb;

    var FieldSourceDocumentLink = BasicFields.FieldChar.extend({
        init: function(parent, name, record) {
            this._super.apply(this, arguments);
        },
        start: function() {
            var self = this;

            if (this.record.data.origin) {
                 this.$el.html('<a>' + this.record.data.origin + '</a>')
            }
        }
    });

    Registry.add('source_document_link', FieldSourceDocumentLink);
});