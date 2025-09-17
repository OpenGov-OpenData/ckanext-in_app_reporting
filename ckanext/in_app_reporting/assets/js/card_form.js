globalThis.cardId = null;
ckan.module('get-metabase-chart-list', function (jQuery) {
    return {
        initialize: function () {
            const that = this;
            that.embeddable_list = this.el.data('embeddable');

            // Populate dropdown
            $.getJSON(this.options.source, function (data) {
                that.collection_items = data.results;
                that.setup();
                // Hide spinner and show select2 dropdown
                $('#chart-loading').hide();
                $('#chart-selection').show();
            }).fail(function() {
                // Show error state if loading fails
                $('#chart-loading').hide();
                $('#chart-selection').show();
                $('#chart-error').show();
            });
        },

        formatResult: function (result) {
            var date = (new Date(result['updated_at']));
            var markup = "<div class='metabase-result'><span class='title'>" + result.name + "</span><span class='modified'>Modified " + date.toLocaleString() + "</span></div>";
            return markup;
        },

        onSelectOption: function(entity_id) {
            var option = $.grep(this.collection_items, function(e){ return e.entity_id == entity_id; })[0];
            $('#field-title').val(option.name).trigger('keyup');
            $('#field-description').val(option.description).trigger('keyup');
            if (this.embeddable_list.includes(option.id)) {
                globalThis.cardId = null;
                $('#publish-warning').html("");
                $('#publish-warning').hide();
            }
            else {
                globalThis.cardId = option.id;
                $('#publish-warning').html("<b>Warning:</b> This card is currently not published. It will be published automatically when you save this resource view.");
                $('#publish-warning').show();
            }
        },

        setup: function () {
            const that = this;
            var settings = {
                width: 'resolve',
                id: 'entity_id',
                dropdownCssClass: 'selectorContainer',
                containerCssClass: 'selectorContainer',
                formatResult: this.formatResult,
                formatSelection: function (result) {
                    return result.name;
                },
                formatNoMatches: this.formatNoMatches,
                formatInputTooShort: this.formatInputTooShort,
                escapeMarkup: function (markup) {
                    return markup;
                },
                matcher: function(term, text) {
                    return text.toUpperCase().indexOf(term.toUpperCase()) >= 0;
                },
                data: this.collection_items
            };

            var select2 = this.el.select2(settings);

            this.el.on("change", function(e) {
                const entity_id = e.target.value;
                that.onSelectOption(entity_id);
            });

            this._select2 = select2;
        },
    };
});

$(document).ready(function () {
    var $form = $('.dataset-resource-form');
    var $addButton = $form.find('button[name="save"]');
    $addButton.on('click', function (event) {
        var cardId = globalThis.cardId;
        if (cardId !== null) {
            event.preventDefault();
            $.ajax({
                method: 'POST',
                url: '/api/action/metabase_card_publish',
                data: JSON.stringify({ 'id': cardId }),
                contentType: 'application/json',
                success: function (response) {
                    $form.submit();
                },
                error: function (error) {
                    console.error('Error publishing card:', error);
                    alert('Failed to publish card.');
                }
            });
        }
    });
});