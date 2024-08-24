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

function aggiungi_camera(proprieta_id) {
    num_ospiti = document.getElementById('num_ospiti').value
    prezzo = document.getElementById('prezzo').value
    fetch('/addRoom', {
        method: 'POST',
        body: JSON.stringify(
            {proprieta_id: proprieta_id, num_ospiti: num_ospiti, prezzo: prezzo}
        )
    }).then((_res) => {
        window.location.reload()
    });
}



function removeAmenity(nome, proprietaid) {
    fetch('/removeAmenity', {
        method: 'POST',
        body: JSON.stringify(
            {nome: nome, proprietaid: proprietaid}
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



