# Convert .docx files to .pdf with Microsoft Word (Windows).
# Usage:  powershell -File src/docx_to_pdf.ps1 student_review.docx REPORT.docx
param([Parameter(ValueFromRemainingArguments = $true)] [string[]] $Files)

$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    foreach ($f in $Files) {
        $in = (Resolve-Path $f).Path
        $out = [System.IO.Path]::ChangeExtension($in, ".pdf")
        $doc = $word.Documents.Open($in, $false, $true)   # read-only
        $doc.SaveAs([ref] $out, [ref] 17)                  # 17 = PDF
        $doc.Close($false)
        Write-Output "wrote $out"
    }
}
finally {
    $word.Quit()
}
