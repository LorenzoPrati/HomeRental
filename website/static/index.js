function removeRoom(camera_id) {
    fetch('/removeRoom', {
        method: 'POST',
        body: JSON.stringify(
            {camera_id: camera_id}
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
    nome = document.getElementById('elimina_amenita').value
    fetch('/aggiungi_amenita', {
        method: 'POST',
        body: JSON.stringify(
            {nome: nome, id_proprieta: id_proprieta}
        )
    }).then((_res) => {
        window.location.reload()
    });
}

function rimuovi_proprieta(proprietaid) {
    fetch('/rimuovi_proprieta', {
        method: 'POST',
        body: JSON.stringify(
            {proprietaid: proprietaid}
        )
    }).then((_res) => {
        window.location.reload()
    });
}



