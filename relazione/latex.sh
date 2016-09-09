old="automatic_rebuild_pdf"

while true; do
    sleep 1
    new=`shasum relazione.tex | awk {' print $1 '}`

    if [ $old != $new ]; then
        old=`shasum relazione.tex | awk {' print $1 '}`
        echo "rebuild pdf";
        pdflatex -interaction nonstopmode relazione.tex
    fi;
done
