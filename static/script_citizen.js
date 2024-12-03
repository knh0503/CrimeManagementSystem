document.getElementById("inquiry_crime_menu").addEventListener("click", function() {
    var containers = document.getElementsByClassName("container");
    for (var i = 0; i < containers.length; i++) {
        containers[i].style.display = "none";
    }
    document.getElementById("inquiry_crime").style.display = "block";
});

document.getElementById("notify_crime_menu").addEventListener("click", function() {
    var containers = document.getElementsByClassName("container");
    for (var i = 0; i < containers.length; i++) {
        containers[i].style.display = "none";
    }
    document.getElementById("notify_crime").style.display = "block";
});

document.getElementById("inquiry_offender_location_menu").addEventListener("click", function() {
    var containers = document.getElementsByClassName("container");
    for (var i = 0; i < containers.length; i++) {
        containers[i].style.display = "none";
    }
    document.getElementById("inquiry_offender_location").style.display = "block";
});

document.getElementById("witness_victim_inquiry_menu").addEventListener("click", function() {
    var containers = document.getElementsByClassName("container");
    for (var i = 0; i < containers.length; i++) {
        containers[i].style.display = "none";
    }
    document.getElementById("witness_victim_inquiry").style.display = "block";
});

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById("check_id_form").addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);

        axios.post('/check_id', formData)
        .then(function(response) {
            const flag = response.data.flag;
            const msg = response.data.msg;
            const region = response.data.region;
            if (flag == 'success') {
                document.getElementById("select_container").style.display = "flex";
                document.getElementById('region').value = region;
                swal.fire({
                    html: msg.replace(/&lt;br&gt;/g, '<br>').replace(/&lt;/g, '<').replace(/&gt;/g, '>'),
                    icon: "info",
                    showCloseButton: true,
                    confirmButtonText: "확인"
                });
            }
            else if (flag == 'fail') {
                swal.fire({
                    title: "오류",
                    html: msg.replace(/&lt;br&gt;/g, '<br>').replace(/&lt;/g, '<').replace(/&gt;/g, '>'),
                    icon: "error",
                    confirmButtonText: "확인"
                });
            }
        })
        .catch(function(error) {
            console.error('Error:', error);
            let errorMessage = "오류가 발생했습니다.";
            if (error.response && error.response.data) {
                errorMessage = error.response.data.replace(/&lt;br&gt;/g, '<br>').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
            }
            swal.fire({
                title: "오류",
                html: errorMessage,
                icon: "error",
                confirmButtonText: "확인"
            });
        });      
    });
});

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById("inquiry_crime_form").addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);

        axios.post('/inquiry_crime', formData)
        .then(function(response) {
            const crime_html = response.data.crime_html;
            const msg = response.data.msg;
            if (msg === '') {
                document.getElementById("inquiry_crime_table").style.display = "block";
                document.getElementById("inquiry_crime_table_body").innerHTML = crime_html;
            }
            else if (crime_html ==='') {
                swal.fire({
                    title: "오류",
                    html: msg.replace(/&lt;br&gt;/g, '<br>').replace(/&lt;/g, '<').replace(/&gt;/g, '>'),
                    icon: "error",
                    confirmButtonText: "확인"
                });
            }
        })
        .catch(function(error) {
            console.error('Error:', error);
        });      
    });
});

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById("notify_crime_form").addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);

        axios.post('/notify_crime', formData)
        .then(function(response) {
            swal.fire({
                title: "접수 완료",
                html: response.data.replace(/&lt;br&gt;/g, '<br>').replace(/&lt;/g, '<').replace(/&gt;/g, '>'),
                icon: "info",
                confirmButtonText: "확인"
            });
        })
        .catch(function(error) {
            console.error('Error:', error);
            let errorMessage = "오류가 발생했습니다.";
            if (error.response && error.response.data) {
                errorMessage = error.response.data.replace(/&lt;br&gt;/g, '<br>').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
            }
            swal.fire({
                title: "오류",
                html: errorMessage,
                icon: "error",
                confirmButtonText: "확인"
            });
        });      
    });
});

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById("inquiry_offender_location_form").addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);

        axios.post('/inquiry_offender_location', formData)
        .then(function(response) {
            const msg = response.data.msg;
            const wanted_offender_html = response.data.wanted_offender_html;
            if (msg === '') {
                document.getElementById("inquiry_offender_location_table").style.display = "block";
                document.getElementById("inquiry_offender_location_table_body").innerHTML = wanted_offender_html;
            }
            else if (wanted_offender_html ==='') {
                swal.fire({
                    title: "오류",
                    html: msg.replace(/&lt;br&gt;/g, '<br>').replace(/&lt;/g, '<').replace(/&gt;/g, '>'),
                    icon: "error",
                    confirmButtonText: "확인"
                });
            }
        })
        .catch(function(error) {
            console.error('Error:', error);
            let errorMessage = "오류가 발생했습니다.";
            if (error.response && error.response.data) {
                errorMessage = error.response.data.replace(/&lt;br&gt;/g, '<br>').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
            }
            swal.fire({
                title: "오류",
                html: errorMessage,
                icon: "error",
                confirmButtonText: "확인"
            });
        });      
    });
});

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById("witness_victim_inquiry_form").addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);

        axios.post('/witness_victim_inquiry', formData)
        .then(function(response) {
            const msg = response.data.msg;
            const crime_html = response.data.crime_html;
            const offender_html = response.data.offender_html;

            // 해당하는 ID를 못 찾았을 경우 알람창
            if (msg !== null) {
                document.getElementById("witness_victim_inquiry_crime_table").style.display = "none";
                document.getElementById("witness_victim_inquiry_offender_table").style.display = "none";
                swal.fire({
                    title: "오류",
                    html: msg.replace(/&lt;br&gt;/g, '<br>').replace(/&lt;/g, '<').replace(/&gt;/g, '>'),
                    icon: "error",
                    confirmButtonText: "확인"
                });
            }
            else {
                document.getElementById("witness_victim_inquiry_crime_table").style.display = "block";
                document.getElementById("witness_victim_inquiry_crime_table_body").innerHTML = crime_html;
                // 범인이 잡히지 않아 offender 정보가 없을 경우
                if (offender_html == null) {
                    document.getElementById("witness_victim_inquiry_offender_table").style.display = "none";
                    swal.fire({
                        text: "범인을 아직 검거하지 못하여 범인에 대한 정보를 제공할 수 없음을 양해해 주시기 바랍니다. 추가적인 수사가 진행 중이며, 범인이 검거되는 대로 신속하게 정보를 공유하도록 하겠습니다.",
                        icon: "info",
                        confirmButtonText: "확인"
                    });
                }
                else {
                    document.getElementById("witness_victim_inquiry_offender_table").style.display = "block";
                    document.getElementById("witness_victim_inquiry_offender_table_body").innerHTML = offender_html;
                }
            }
        })
        .catch(function(error) {
            console.error('Error:', error);
            let errorMessage = "오류가 발생했습니다.";
            if (error.response && error.response.data) {
                errorMessage = error.response.data.replace(/&lt;br&gt;/g, '<br>').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
            }
            swal.fire({
                title: "오류",
                html: errorMessage,
                icon: "error",
                confirmButtonText: "확인"
            });
        });      
    });
});

function crime_data_lookup() {
    document.getElementById("inquiry_crime_data").style.display = "block";
    document.getElementById("inquiry_crime_form").style.display = "none";
    document.getElementById("inquiry_crime_table").style.display = "none";

    const region = document.getElementById('region').value;
    axios.post('/crime_data_lookup', {
        region : region
    })
    .then(function (response) {
        // 그래프로 보여주기
        const year_list = response.data.year_crime_data.map(item => item.year);
        const year_cnt_list = response.data.year_crime_data.map(item => item.count);
        let year_chart = document.getElementById('year_chart');
        let myChart = new Chart(year_chart, {
            type: 'bar',
            data: {
              labels: year_list,
              datasets: [
                {
                  label: 'year_cnt',
                  data: year_cnt_list,
                }
              ]
            },
          });

          const month_list = response.data.month_crime_data.map(item => item.month);
          const month_cnt_list = response.data.month_crime_data.map(item => item.count);
          let month_chart = document.getElementById('month_chart');
          let myChart2 = new Chart(month_chart, {
              type: 'bar',
              data: {
                labels: month_list,
                datasets: [
                  {
                    label: 'month_cnt',
                    data: month_cnt_list,
                  }
                ]
              },
            });
    })
    .catch(function(error) {
        console.error('Error:', error);
        let errorMessage = "오류가 발생했습니다.";
        if (error.response && error.response.data) {
            errorMessage = error.response.data.replace(/&lt;br&gt;/g, '<br>').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
        }
        swal.fire({
            title: "오류",
            html: errorMessage,
            icon: "error",
            confirmButtonText: "확인"
        });
    }); 

}

function crime_record_lookup() {
    document.getElementById("inquiry_crime_data").style.display = "none";
    document.getElementById("inquiry_crime_form").style.display = "block";
    document.getElementById("inquiry_crime_table").style.display = "none";
}