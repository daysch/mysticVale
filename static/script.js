function setup() {
    createAccordion();
    setup_modal();
    if (typeof window.interval == 'undefined') {
        window.interval = window.setInterval(check_server, 1000);
    }
}

function setup_modal() {
    // modal boxes on right click of image
    // Get the modal
    var modal = document.getElementById("myModal");
    var modalImg = document.getElementById("modalImg");

    // Get the image and insert it inside the modal when img is right clicked
    $('img').bind('contextmenu', function() {
        event.preventDefault();
        modal.style.display = "block";
        modalImg.src = this.src;
    });

    // When the user clicks anywhere, close the modal
    modal.onclick = function() {
      modal.style.display = "none";
    };

}

// Return selected item to original state
function deselectSelection(move_to_back = true) {
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
        if (move_to_back) {
            adv_elmt.parent().children().first().after(adv_elmt);
        }
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
    $('#add-to-deck-bottom').prop('disabled',true);
    $('#discard-card').prop('disabled',true);
    $('#discard-card-deck').prop('disabled',true);
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
        replaceHTML(data,['field','deck-display','discard']);
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

        replaceHTML(data,['field','deck-display','discard']);
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
        $.get('/move', {'source':source,'item':selection,'destination':'purgatory','source_card':source_card}, function(data) {
        replaceHTML(data);
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
            advancement.find('img').attr('onclick',`selCardAdv('${card_id}','${location}')`);
            if (source != 'purgatory') {
                $('#player').find('#'+card_id).parent().before(advancement);
            }
            else {
                $('#player').find('#'+selection).remove();
                $('#player').find('#'+card_id).parent().before(`<div class="cardAdv" id="${selection}">
                                        <img src="https://flaskdixit.files.wordpress.com/2020/08/${selection.slice(0,6)}.png" class="advancement" onclick="selCardAdv('${card_id}','${location}')">
                                       </div>`);
            }
            deselectSelection(false);
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
        $('#add-to-deck-bottom').removeAttr('disabled');
        $('#discard-card').removeAttr('disabled');
        $('#discard-card-deck').removeAttr('disabled');
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
    $.get('/action', {'action':'end_turn'}, function() {});
}

function discardCard() {
    $.get('/move', {'source':source,'item':selection,'destination':'discard','source_card':null}, function(data) {
        replaceHTML(data, ['deck-display','field','purgatory','discard']);
        if ($('#deck').is(':visible')) {
            toggleDeck();
        }
    });
}

function discardVale() {
    $.get('/action', {'action':'discard_vale','vale':selection, 'source':source},function(data) {
            replaceHTML(data, ['vales-owned']);
        });
}

function addToDeck() {
    $.get('/move', {'source':source,'item':selection,'destination':'deck','source_card':null}, function(data) {
        replaceHTML(data, ['deck-display','field','purgatory','discard']);
    });
}

function addToDeckBottom() {
    $.get('/move', {'source':source,'item':selection,'destination':'deck_bottom','source_card':null}, function(data) {
        replaceHTML(data, ['deck-display','field','purgatory','discard']);
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
    deselectSelection(false);
    source = location;
    selection = id;
    $('#player').find('#'+id).css('background','#ebebe0');

    $('#deselect').removeAttr('disabled');

}

// Buy selected vale card
function buyVale(id) {
    $.get('/buy', {'valeID': id}, function(num_vales) {
        $('#'+id).attr('src','https://flaskdixit.files.wordpress.com/2020/08/blank_advancement.png');
        $('#'+id).removeAttr('onclick');
        $('#'+id).removeAttr('id');
        $('#player').find('#vales-owned div').append('<img src="https://flaskdixit.files.wordpress.com/2020/08/'+id+'.png" class="vale" style="width:15%" id ="'+id+'" onclick="selectVale(\''+id+'\',\'vales\')">');
        $('#vales-owned').prev().html(`Vales Owned (${num_vales} vale${num_vales != 1 ? 's':''})`);
    });
}

function shuffle() {
    // shuffle deck
    $.get('/action', {'action':'shuffle'}, function(data) {
        replaceHTML(data, ['deck-display','discard','field']);
    });
}

function undo() {
    $.get('/action', {'action':'undo','number':$('#undo-number').val()}, function(data) {
        replaceHTML(data);
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
        deselectSelection(false);
    });
}

function setLeader(leader) {
    $.get('/action', {'action':'set_leader','leader':leader}, function() {
        window.location.replace('/play');
    });
}

function discardField() {
    $.get('/action',{'action':'discard_field'}, function(data) {
        replaceHTML(data, ['field','discard']);
    });
}

function replaceHTML(data,places=null) {
    if (!places) {
        document.open("text/html", "replace");
        document.write(data['full_html']);
        document.close();
        setup_modal();
    }
    else {
        for (var place of places) {
            if (data[place]) {
                if (data[place] == 'advancements' && source == 'adv_deck') {
                    deselectSelection(false);
                }
                else if (place == 'vales-owned') {
                    $('#vales-owned').prev().html(`Vales Owned (${data['num_vales']} vale${data['num_vales'] != 1 ? 's':''})`);
                }
                else if (place == 'discard') {
                    $('#discard').prev().html(`Your Discard (${data['num_discard']} card${data['num_discard'] != 1 ? 's':''})`);
                }
                $('#'+place).html(data[place]);
            }
        }
    }
    setup_modal();
}

function check_server() {
    for (player of player_ids) {
        $.ajax({
             url: '/update',
             async: false,
             type: 'GET',
             data : {'player':player},
             success: function(data) {
                // new player's turn
                if (data.full_html) {
                  replaceHTML(data);
                }

                // let user know if it's newly someone's turn
                if (data.turn_name) {
                    window.alert(`It's ${data.turn_name}'s turn!`);
                }

                else if (data.your_turn) {
                    window.alert(`It's your turn!`);
                }

                // need to update one player's field
                else if (data.requested_field) {
                  hidden = $(`#player${player}`).is(':hidden');
                  $(`#player${player}`).html(data.requested_field);
                  replaceHTML(data,['advancements','vales-available']);
                  if (!hidden) {
                    $(`#player${player}`).display = 'block';
                    $(`#player${player}`).prev().removeClass('active');
                  }
                  else {
                    $(`#player${player}`).display = 'none';
                    $(`#player${player}`).prev().addClass('active');
                  }
                }
             }
        });
    }
}