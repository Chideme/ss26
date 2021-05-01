window.onload = function(){
  document.getElementById('clickbutton').click()
}
document.addEventListener('DOMContentLoaded',() => {
  document.querySelector('#form').onsubmit = () => {
    const request = new XMLHttpRequest()
    const start_date = document.querySelector('#start_date').value;
    const end_date = document.querySelector('#end_date').value;
    const frequency = document.querySelector('#frequency').value;
    request.open('POST','/dashboard/finance_reports');

    
    // when request finishes
    request.onload = () => {

      const report = JSON.parse(request.responseText);
      var cash_dates = report.CashDate;
      var cash_data = report.CashData;
      var sales_dates = report.SalesDates;
      var sales_data = report.SalesData;
      var margin_dates = report.MarginDates;
      var margin_data = report.MarginData;
      var assets = report.Assets;
      var liabilities= report.Liabilities;
      
      console.log(sales_dates);

          var ctx = document.getElementById("CashBalances");
          var cChart = new Chart(ctx, {
            type: 'line',
            data: {
              labels: cash_dates,
              datasets: [{
                data: cash_data,
                lineTension: 0,
                backgroundColor: '#333',
                borderColor: 'rgba(0,0,255,1)',
                borderWidth: 4,
                pointBackgroundColor: '#007bff'
              }]
            },
            options: {
              scales: {
                yAxes: [{
                  ticks: {
                    beginAtZero: true
                  }
                }]
              },
              legend: {
                display: false,
              },
              title: {
                display:true,
                fontColor: 'rgba(255,255,255,255)',
                fontStyle: 'bold',
                text:frequency.concat(' ','Cash ','Balances ($)')
              }
            }
          });
          var r_ctx = document.getElementById("Revenue");
          var rChart = new Chart(r_ctx, {
            type: 'line',
            data: {
              labels: sales_dates,
              datasets: [{
                data: sales_data,
                lineTension: 0,
                backgroundColor: '#333',
                borderColor: 'rgba(11,156,49,1)',
                borderWidth: 4,
                pointBackgroundColor: '#007bff'
              }]
            },
            options: {
              scales: {
                yAxes: [{
                  ticks: {
                    beginAtZero: true
                  }
                }]
              },
              legend: {
                display: false,
              },
              title: {
                display:true,
                fontColor: 'rgba(255,255,255,255)',
                fontStyle: 'bold',
                text:'Revenue ($)'
              }
            }
          });
          var p_ctx = document.getElementById("NetProfit");
          var pChart = new Chart(p_ctx, {
            type: 'line',
            data: {
              labels: margin_dates,
              datasets: [{
                data: margin_data,
                lineTension: 0,
                backgroundColor: '#333',
                borderColor: 'rgba(255,0,0,255)',
                borderWidth: 4,
                pointBackgroundColor: '#007bff'
              }]
            },
            options: {
              scales: {
                yAxes: [{
                  ticks: {
                    beginAtZero: true 
                  }
                }]
              },
              legend: {
                display: false,
              },
              title: {
                display:true,
                fontColor: 'rgba(255,255,255,255)',
                fontStyle: 'bold',
                text:'Net Profit Margin (%)'
              }
            }
          });

          var a_ctx = document.getElementById("AssetsVsLiabilities");
          var aChart = new Chart(a_ctx, {
            type: 'bar',
            data: {
            
              datasets: [{
                label:'Assets',
                data: assets,
                lineTension: 0,
                backgroundColor: 'rgba(11,156,49,1)',
                borderColor: 'rgba(11,156,49,1)',
                borderWidth: 4,
                pointBackgroundColor: '#007bff'
              },
              {
                label:'Liabilities',
                data: liabilities,
                lineTension: 0,
                backgroundColor: 'rgba(255,0,0,255)',
                borderColor: 'rgba(255,0,0,255)',
                borderWidth: 4,
                pointBackgroundColor: '#007bff'
              }]
            },
            options: {
              scales: {
                yAxes: [{
                  ticks: {
                    beginAtZero: true
                  }
                }]
              },
              legend: {
                display: true,
                labels: {
                  fontColor: 'rgba(255,255,255,255)',
                },
              position:'bottom'
              },
              title: {
                display:true,
                fontColor: 'rgba(255,255,255,255)',
                fontStyle: 'bold',
                text:'Assets Vs Liabilities  ($)'
              }
            }
          });

    }

    const data = new FormData();
    data.append('start_date',start_date);
    data.append('end_date',end_date);
    data.append('frequency',frequency);
    
    //send request
    request.send(data);

    return false;  

    }
    
    });

