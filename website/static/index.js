function removeBed(bedid) {
    fetch('/removeBed', {
        method: 'POST',
        body: JSON.stringify(
            {id: bedid}
        )
    }).then((_res) => {
        window.location.reload()
    });
}

function removeRoom(ordinale, proprietaid) {
    fetch('/removeRoom', {
        method: 'POST',
        body: JSON.stringify(
            {ordinale: ordinale, proprietaid: proprietaid}
        )
    }).then((_res) => {
        window.location.reload()
    });
}

function addRoom(proprietaid) {
    fetch('/addRoom', {
        method: 'POST',
        body: JSON.stringify(
            {proprietaid: proprietaid}
        )
    }).then((_res) => {
        window.location.reload()
    });
}

function addBed(ordinalecamera, proprietaid) {
    fetch('/addBed', {
        method: 'POST',
        body: JSON.stringify(
            {ordinalecamera: ordinalecamera, proprietaid: proprietaid}
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

