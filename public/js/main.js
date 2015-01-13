// establish 'wootpaste' namespace
var wootpaste = wootpaste = wootpaste || {};

// load wootpaste when page is fully loaded
$(function () {
  wootpaste.load();
});

wootpaste.load = function () {
  // - reserved for the future, load requirements etc. -
  wootpaste.init();
};

wootpaste.init = function () {
  wootpaste.displayQRCode();

  wootpaste.registerPrivateChange();

  if (document.location.hash.length > 1) {
    wootpaste.passphrase = document.location.hash.substring(1);
    if (wootpaste.passphrase) {
      // need to rewrite links with the passphrase:
      var appendHref = function (sel) {
        sel.attr('href', sel.attr('href') + '#' + wootpaste.passphrase)
      };
      appendHref($('a[href^="/paste/"]'));
      appendHref($('a[href^="/edit/"]'));
    }
  }

  wootpaste.decryptContent();
  if ($('#content_ace').length > 0 && wootpaste.settings['ace']) {
    wootpaste.initAce();
    wootpaste.ace_editor.focus();
  }
  $('.autofocus').focus();
  var path = window.location.pathname;

  if (path.indexOf('/settings') == 0) {
    wootpaste.initSettings();
  }
  // create and update forms need to encrypt paste and submit via xhr
  if ($('form[name="paste"]').length > 0) {
    wootpaste.initPasteForm();
  }

  $('#content_ace, textarea#content').keydown(function (e) {
    if (e.keyCode == 13) {
      if (e.shiftKey) {
        $('#paste_submit').click();
        e.preventDefault();
      }
    }
  });
  $('input[name="subject"]').hide();
};

wootpaste.initAce = function () {
  $('textarea#content').hide();
  $('div#content_ace').show();

  console.log('[wootpaste] init ace editor');
  var editor = wootpaste.ace_editor = ace.edit('content_ace');
  var session = editor.getSession();
  session.setValue($('textarea#content').val());

  editor.setTheme('ace/theme/chrome');
  // syncronize the ace editor content with the textarea
  session.on('change', function (e) {
    $('textarea#content').val(session.getValue());
  });
};

// init specific to settings page
wootpaste.initSettings = function () {
  // pygment style preview
  $('#pygment_style').on('change', function (e) {
    $('link[href^="/pygments/"]').attr('href', '/pygments/'+$(this).val()+'.css');
  });
};

// encrypt paste before sending it via xhr, redirect with client-side passphrase hash
wootpaste.initPasteForm = function () {
  var form = $('form[name="paste"]');
  form.on('submit', function (e) {
    if ($('#encrypted').is(':checked')) {
      e.preventDefault();
      console.log('[wootpaste] submit paste form');

      if (!wootpaste.passphrase) {
        wootpaste.passphrase = wootpaste.genPassphrase(64);
      }

      // encrypt textarea in place:
      wootpaste.encryptContent();

      // 
      $.ajax({
        url: form.attr('action'),
        type: 'POST',
        data: form.serialize(),
        success: function (res) {
          window.location = res['url'] + '#' + wootpaste.passphrase;
        }
      });
    }
  });
};

wootpaste.genPassphrase = function (len) {
  var alph = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_';
  // alph.length == 64
  var passphrase = '';
  // generate passphrase:
  for (var i = 0; i < len; i++) {
      var r = sjcl.random.randomWords(1) & 0x3F;
      // r = 32 bits (4 bytes), [600508984, -569387533, -1791877151, 1128147583, -1710388734]
      var x = r % 64;
      passphrase += alph[ x ];
  }
  return passphrase;
};

wootpaste.encryptContent = function () {
  if (!wootpaste.passphrase) throw 'uninitialized passphrase!';
  var content = $('#content').val();
  var encrypted = sjcl.encrypt(wootpaste.passphrase, content);
  $('#content').val(encrypted);
  // wootpaste.ace_editor.getSession().setValue(encrypted);
};

wootpaste.decryptContent = function () {
  if ($('.encrypted_content').length > 0) {
    var encrypted = $('.encrypted_content').html();
    //console.log(encrypted);
    //console.log(wootpaste.passphrase);
    $('.encrypted_content').text(sjcl.decrypt(wootpaste.passphrase, encrypted));
  }
};

wootpaste.registerPrivateChange = function () {
  var change_submit = function (private) {
    var submit_button = $('#paste_submit');
    if (private) {
      submit_button.addClass('button_secondary');
      submit_button.text('Create Private');
    }
    else {
      submit_button.removeClass('button_secondary');
      submit_button.text('Create Public');
    }
  };
  var change_private = function (private) {
    $('input#private').prop('checked', private);
  };

  $('input#private').change(function (event) {
    change_submit($(this).is(':checked'));
  });
  $('#paste_submit').text('Create Public');

  $('input#encrypted').change(function (event) {
    var set_private = $(this).is(':checked');
    if (set_private) {
      $('label input#irc_announce').parent().hide().attr('checked', false);
    }
    else {
      $('label input#irc_announce').parent().show();
    }
    change_submit(set_private);
    change_private(set_private);
    $('input#private').prop('disabled', set_private);
  });
};

wootpaste.displayQRCode = function () {
    var render = function () {
        var url = window.location.href;
        console.log(url);
        var size = (window.location.hash.length > 1) ? 200 : 150;
        $('#paste_qrcode').qrcode({
            "width": size,
            "height": size,
            "color": "#3a3",
            "text": url
        });
        $('#paste_qrcode_show').hide();
    };
    $('#paste_qrcode_show').click(function (event) {
        wootpaste.settings.show_qrcode = true;
        render();
        event.preventDefault();
    }).show();
    if (wootpaste.settings.show_qrcode) {
        render();
    }
};

