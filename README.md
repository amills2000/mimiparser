# mimiparser

mimiparser is an small Python code ment to parse and unify in a sort of tidy way the results of some of the mimikatz outputs to help keep track of the users gotten and where they came from.

## Installation

Install the requirements 

```bash
pip install -r .\requirements.txt
```

## Usage

The idea is to have a folder with all the full output of the mimikatz execution on several machines and execute this tool to merge them together. It is important to save the mimikatz results with meaningful names that help you identify the source. 

This option will overwrite any previous parsing performed
```bash
py .\parse_mimi.py -d "<path-to-mimikatz-folder>"
```
If you want to be asked before overwriting, you can use the parameter
```bash
py .\parse_mimi.py -d "D:\cursos\alteredsecurity\crtp\mimis" -f False
```

## License

[MIT](https://choosealicense.com/licenses/mit/)