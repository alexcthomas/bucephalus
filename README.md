# Highcharts

Dynamic data visualization with Flask, Highcharts. Improved examples in official tutorial by using AJAX to update data. Data updating by querying a database is straightforward under this framework. 

## Screenshot

![alt text](static/img/spline.png)

![alt text](static/img/stock.png)

## Troubleshooting

-   **Uncaught ReferenceError: $ is not defined**

Make sure that `<script>...</script>` is put like
    
    {% block scripts%}
        {{ super() }}
        <script>
            //your script
        </script>
    {% endblock %}

It is important to put **`{{ super() }}`** before script in order to not overriding the `script` block defined by `bootstrap`.
