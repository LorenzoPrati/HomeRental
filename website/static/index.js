function rimuovi_camera(id_camera) {
    fetch('/rimuovi_camera', {
        method: 'POST',
        body: JSON.stringify(
            {id_camera: id_camera}
        )
    }).then((_res) => {
        window.location.reload()
    });
}

function aggiungi_camera(id_proprieta) {
    num_ospiti = document.getElementById('num_ospiti').value
    prezzo_per_notte = document.getElementById('prezzo_per_notte').value
    fetch('/aggiungi_camera', {
        method: 'POST',
        body: JSON.stringify(
            {id_proprieta: id_proprieta, num_ospiti: num_ospiti, prezzo_per_notte: prezzo_per_notte}
        )
    }).then((_res) => {
        window.location.reload()
    });
}

function rimuovi_amenita(nome, id_proprieta) {
    fetch('/rimuovi_amenita', {
        method: 'POST',
        body: JSON.stringify(
            {nome: nome, id_proprieta: id_proprieta}
        )
    }).then((_res) => {
        window.location.reload()
    });
}

function aggiungi_amenita(id_proprieta) {
    nome = document.getElementById('aggiungi_amenita').value
    fetch('/aggiungi_amenita', {
        method: 'POST',
        body: JSON.stringify(
            {nome: nome, id_proprieta: id_proprieta}
        )
    }).then((_res) => {
        window.location.reload()
    });
}

function rimuovi_proprieta(id_proprieta) {
    fetch('/rimuovi_proprieta', {
        method: 'POST',
        body: JSON.stringify(
            {id_proprieta: id_proprieta}
        )
    }).then((_res) => {
        window.location.reload()
    });
}



