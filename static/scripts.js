

$(document).ready(function(){
        $('a[data-toggle="tab"]').on('shown.bs.tab', function(e){
            localStorage.setItem('activeTab', $(e.target).attr('href'));
        });

        // Here, save the index to which the tab corresponds. You can see it 
        // in the chrome dev tool.
        var activeTab = localStorage.getItem('activeTab');

        // In the console you will be shown the tab where you made the last 
        // click and the save to "activeTab". I leave the console for you to 
        // see. And when you refresh the browser, the last one where you 
        // clicked will be active.
        

        if (activeTab) {
           $('.nav-tabs a[href="' + activeTab + '"]').tab('show');
        }

        //Prints Driveway
        function printTable (){
            var toprint = document.getElementById('printTable');
            newWIn = window.open("");
            newWIn.document.write('<html><body>');
            newWIn.document.write('<link rel="stylesheet" href="/static/vendor/bootstrap/css/bootstrap.min.css"/>');
            newWIn.document.write('<link href="/static/style.css" rel="stylesheet">');
            newWIn.document.write(toprint.innerHTML);
            newWIn.document.write('</body></html>');
            newWIn.print();
            newWIn.close();
        };
        $('#print').on('click',function(){
            printTable();
            
        });

        

        // return to page position after reload ( for driveway updates)
        
        var scrollpos = localStorage.getItem('scrollpos');
        if (scrollpos) window.scrollTo(0,scrollpos);

        window.onbeforeunload = function(e) {
            localStorage.setItem('scrollpos',window.scrollY);
        };
        
        
        // DataTables function
        $('#export').DataTable( {
            dom: '<Blf<t>ip>',
            "lengthMenu": [ 200, 150, 100, 75],
            buttons: [
                'copy',
                'excel',
                'csv',
                'pdf'
            ]
        } );

        // Statement DataTables function
        
         $('#statement').DataTable( {
            dom: '<f<t>liBp>',
            buttons: [
                'copy',
                'excel',
                'csv',
                'pdf'
                ],
                "columnDefs": [
                    {
                    // The `data` parameter refers to the data for the cell (defined by the
                    // `data` option, which defaults to the column being worked with, in
                    // this case `data: 0`.
                    "targets": 4,
                    data: 0,
                    "render": function ( data, type, row, meta ) {
                            if (meta.row == 0 ) {
                                return row[4];
                            } else {
                                var i = (Number(meta.settings.aoData[meta.row-1].anCells[4].innerText));
                                console.log(i)
                                return Number(i + Number(row[2])-Number(row[3]));
                            }
                        
                           
                        },
                    
                    }  
                
            ]
            } );
            
            
            
            

             
            
// html2pdf
$('#download').on('click',function(){
            var element = document.getElementById('printTable');
            var opt = {
            margin:       [1,1,1,1],
            filename:     'driveway.pdf',
            html2canvas:  { scale: 2, bottom: 0 },
            jsPDF:        { unit: 'mm', format: 'a4', orientation: 'landscape' },
            pagebreak: { before: '#dont'}
            };

          
            // Old monolithic-style usage:
                html2pdf(element, opt);
            })

           
    });