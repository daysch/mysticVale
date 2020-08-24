// Return selected item to original state
function deselectSelection() {
    if (!selection) {
        return;
    }

    // deselect advancement from deck
    if (selection[0] == 'a' && source == 'adv_deck') {
        $('#'+selection).removeAttr('style');
    }

    // deselect card advancement
    else if (selection[0] == 'a' && source_card) {
        var adv_elmt = $('#player').find('#'+selection);
        adv_elmt.css('background','');
        adv_elmt.parent().children().first().after(adv_elmt);
    }

    // deselect purgatory advancement
    else if (selection[0] == 'a') {
        adv_elmt = $('#player').find('#'+selection);
        adv_elmt.css('background','');
    }

    // deselect card (including disable buttons)
    else if (selection[0] == 'c') {
        $('#player').find('#'+selection).parent().parent().removeClass('selected-card');
    }

    // deselect vale
    else if (selection[0] == 'v') {
        $('#player').find('#'+selection).removeClass('selected-vale');
    }

    // disable button
    $('#add-to-deck').prop('disabled',true);
    $('#discard-card').prop('disabled',true);
    $('#deselect').prop('disabled',true);
    $('#discard-vale').prop('disabled',true);
    $('#move-to-vales').prop('disabled',true);
    $('#move-to-purgatory').prop('disabled',true);
    $('#flip-leader').prop('disabled',true);

    source = null;
    selection = null;
    source_card = null;
}

function pushCard() {
    $.get('/action', {'action':'push'}, function(data) {
        // select card
        var on_deck = $('#player').find(".on-deck");
        on_deck.removeClass('on-deck');

        // update button
        var button =  on_deck.find('button');
        button.attr('onclick',`selectCard('${button.attr('id')}','field')`);
        button.html(`^Select Card`);


        // add on deck image
        if (data.color) {
            on_deck.before(`<span class="card on-deck">
                                <div class="cardAdv">
                                    <img src="https://flaskdixit.files.wordpress.com/2020/08/${data.color}_background.png" class="advancement">
                                </div>
                                <div class="card-select">
                                    <button type="button" onclick="flipCard()" id="flip">Flip (${data.remaining} Left)</button>
                                </div>
                            </span>`);
        }
        else {
            on_deck.before(`<span class="card on-deck">
                                <div class="cardAdv">
                                    <img src="https://flaskdixit.files.wordpress.com/2020/08/blank_advancement.png" class="advancement">
                                </div>
                                <div class="card-select"><button type="button" onclick="flipCard()" id="flip">Shuffle and Flip</button></div>
                            </span>`);
        }
        // update advancement clickability
        on_deck.find('img').each(function(){
            $(this).attr('onclick',`selCardAdv('${on_deck.find('button').attr('id')}','field')`);

        });

        // put card in field
        parent = on_deck.parent();
        parent.append(on_deck.first());
    });
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}


function flipCard() {
    $.get('/action', {'action':'flip'}, function(data) {
        if (!data) {
            alert('All your cards are in play!');
            return;
        }

        // move card from (hidden) deck
        var on_deck = $('#field').find('.on-deck');
        new_on_deck = $('#deck .panel').find('.card').last();
        if (!new_on_deck.length) {
            return window.location.replace('/play');
        }
        on_deck.before(new_on_deck);

        on_deck.remove();

        // update card
        var id = new_on_deck.find('button').attr('id');
        new_on_deck.find('img').attr('onclick',`"selCardAdv('${id}','field')"`);
        new_on_deck.addClass('on-deck');
        new_on_deck.find('button').attr('onclick','pushCard()');
        new_on_deck.find('button').html(`Push (${data.remaining} left)`);
    });
}

/* DONE */

function selectVale(vale, location) {
    deselectSelection();

    // visually show vale is selected
    $('#player').find('#'+vale).addClass('selected-vale');

    // select vale
    selection = vale;
    source = location;

    // enable buttons
    $('#deselect').removeAttr('disabled');
    $('#move-to-purgatory').removeAttr('disabled');
    $('#move-to-vales').removeAttr('disabled');
    $('#discard-vale').removeAttr('disabled');
}

function moveToPurgatory() {
        $.get('/move', {'source':source,'item':selection,'destination':'purgatory','source_card':source_card}, function() {
        window.location.replace('/play');
    });
}

// Select card, to move card or to move onto card
function selectCard(card_id, location) {
    // moving advancements to card
    if (selection && selection[0] == 'a' && selection[1] != 'l' && location == 'field') {
        // from advancements available for purchase
        if (source == 'adv_deck') {
            $.get('/move', {'source':source, 'item':selection, 'destination':card_id, 'source_card':source_card}, function(data) {
                $('#'+selection).removeAttr('style');
                if (!data[0]) {
                    $('#'+selection).attr('src','https://flaskdixit.files.wordpress.com/2020/08/blank_advancement.png');
                    $('#'+selection).removeAttr('onclick id');
                }
                // update number of FS left
                else {
                    $('#'+selection).parent().find('figcaption').html(data[0]+" left");
                }

                $('#player').find('#'+card_id).parent().before(`<div class="cardAdv" id="${data[1]}">
                                                                  <img src="https://flaskdixit.files.wordpress.com/2020/08/${selection}.png" class="advancement" onclick="selCardAdv('${card_id}','${location}')">
                                                                </div>`);
            deselectSelection();
            });}
        // from elsewhere
        else {
            $.get('/move', {'source':source, 'item':selection, 'destination':card_id, 'source_card':source_card}, function() {
            advancement = $('#player').find('#'+selection);
            advancement.attr('onclick',`selCardAdv('${card_id}','${location})`);
            if (source != 'purgatory') {
                $('#player').find('#'+card_id).parent().before(advancement);
            }
            else {
                $('#player').find('#'+selection).remove()
                $('#player').find('#'+card_id).parent().before(`<div class="cardAdv" id="${selection}">
                                        <img src="https://flaskdixit.files.wordpress.com/2020/08/${selection.slice(0,6)}.png" class="advancement" onclick="selCardAdv('${card_id}','${location}')">
                                       </div>`);
            }
            deselectSelection();
        });}

    }
    // moving card
    else {
        // select card
        deselectSelection();
        selection = card_id;
        source = location;

        // show card has been selected
        $('#player').find('#'+card_id).parent().parent().addClass('selected-card');

        // enable buttons
        $('#add-to-deck').removeAttr('disabled');
        $('#discard-card').removeAttr('disabled');
        $('#deselect').removeAttr('disabled');
        $('#move-to-purgatory').removeAttr('disabled');
    }
}

function moveToVales() {
    $.get('/move',{'source':source,'item':selection,'destination':'vales','source_card':null}, function() {
        $('#player').find('#'+selection).remove();
        $('#player').find('#vales-owned div').append(`<img src="https://flaskdixit.files.wordpress.com/2020/08/${selection}.png" class="vale" style="width:15%" id ="${selection}" onclick="selectVale('${selection}','vales')">`);
    });
}

function selCardAdv(card,location) {
    deselectSelection();
    source_card = card;
    source = location;
    var adv_elmt = $('#player').find('#'+card).parent().prev();
    selection = adv_elmt.attr('id');

    adv_elmt.css('background','black');
    $('#deselect').removeAttr('disabled');
    $('#move-to-purgatory').removeAttr('disabled');

    // leader
    if (selection[1] == 'l' && location == 'field') {
        $('#flip-leader').removeAttr('disabled');
    }
}

function toggleDeck() {
    if ($('#deck').is(':visible')) {
        $('#toggle-deck').html('Show Your Deck');
    }
    else {
        $('#toggle-deck').html('Hide Your Deck');
    }

    $('#deck').toggle();
}

function endTurn() {
    $.get('/action', {'action':'end_turn'}, function() {
        window.location.replace('/play');
    });
}

function discardCard() {
    $.get('/move', {'source':source,'item':selection,'destination':'discard','source_card':null}, function() {
        window.location.replace('/play');
    });
}

function discardVale() {
    $.get('/action', {'action':'discard_vale','vale':selection, 'source':source},function() {
            window.location.replace('/play');
        });
}

function addToDeck() {
    $.get('/move', {'source':source,'item':selection,'destination':'deck','source_card':null}, function() {
        window.location.replace('/play');
    });
}

function createAccordion() {
    var acc = document.getElementsByClassName("accordion");
    var i;

    for (i = 0; i < acc.length; i++) {
      acc[i].addEventListener("click", function() {
        /* Toggle between adding and removing the "active" class,
        to highlight the button that controls the panel */
        this.classList.toggle("active");

        /* Toggle between hiding and showing the active panel */
        var panel = this.nextElementSibling;
        if (panel.style.display === "block") {
          panel.style.display = "none";
        } else {
          panel.style.display = "block";
        }
      });
    }
}

// Select Advancement
function selectAdv(id,location) {
    deselectSelection();
    source = location;
    selection = id;
    $('#player').find('#'+id).css('background','#ebebe0');

    $('#deselect').removeAttr('disabled');

}

// Buy selected vale card
function buyVale(id) {
    $.get('/buy', {'valeID': id}, function(vale) {
        if (vale) {
            $('#'+id).attr('src','https://flaskdixit.files.wordpress.com/2020/08/blank_advancement.png');
            $('#'+id).removeAttr('onclick');
            $('#'+id).removeAttr('id');
            $('#player').find('#vales-owned div').append('<img src="https://flaskdixit.files.wordpress.com/2020/08/'+id+'.png" class="vale" style="width:15%" id ="'+id+'" onclick="selectVale(\''+id+'\',\'vales\')">');
        }
        else {
            alert("Unable to buy vale. That's all I know.");
        }
    });
}

function shuffle() {
    // shuffle deck
    $.get('/action', {'action':'shuffle'}, function() {
        window.location.replace('/play');
    });
}

function flipToken() {
    $.get('/action', {'action':'flip_token'}, function() {});
    if ($('#token').css('background-color') == 'rgb(0, 0, 255)') {
        $('#token').css('background-color', 'gray');
        if ($('#token-star').length != 0) {
            $('#token').css('padding-top','0%');
            $('#token-star').css('display','block');
        }
    }
    else {
        $('#token').css('background-color', 'blue');
        if ($('#token-star').length != 0) {
            $('#token-star').hide();
            $('#token').css('padding-top','5%');
        }
    }

}

function scorePoints() {
    $.get('/action', {'action':'score_points'}, function(response) {
        let score = response[0];
        let points_left = response[1];
        $('#player').find("#score").html('Your score: ' + score);
        $('#player').find("#points-left").html('Points left: ' + points_left);
    });
}

function losePoints() {
    $.get('/action', {'action':'lose_points'}, function(response) {
        let score = response[0];
        let points_left = response[1];
        $('#player').find("#score").html('Your score: ' + score);
        $('#player').find("#points-left").html('Points left: ' + points_left);
    });
}

function addBankPoints() {
    $.get('/action', {'action':'add_bank'}, function(points_left) {
        $('#player').find("#points-left").html('Points left: ' + points_left);
    });
}

function subBankPoints() {
    $.get('/action', {'action':'sub_bank'}, function(points_left) {
        $('#player').find("#points-left").html('Points left: ' + points_left);
    });
}

function flipLeader() {
    $.get('/action', {'action':'flip_leader'}, function(leader) {
        $('#'+selection).children('img').attr('src',`https://flaskdixit.files.wordpress.com/2020/08/${leader}.png`);
        $('#'+selection).attr('id',leader);
        selection = leader
        deselectSelection();
    });
}

function setLeader(leader) {
    $.get('/action', {'action':'set_leader','leader':leader}, function() {
        window.location.replace('/play');
    });
}

function discardField() {
    $.get('/action',{'action':'discard_field'}, function() {
        window.location.replace('/play');
    });
}