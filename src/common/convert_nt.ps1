$month = 0
cat namenstage.txt | ForEach-Object {
    #if ($_.length -eq 0) { continue }
    if ([int][char]$_.toString()[0] -gt 57) { 
        $month += 1
        #Write-Output ("{0}{1}" -f $month, $_)
    }
    if ([int][char]$_.toString()[0] -lt 58 -and [int][char]$_.toString()[0] -gt 47) {
        $day = $_.toString().Substring(0,2).trim('.')
        $names = $_.toString().Substring(3).Trim()
        Write-Output ("{0:00}-{1:00}`t{2}" -f [int]$month, [int]$day, $names)
    }
}