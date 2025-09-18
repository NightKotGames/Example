// Source/Example/Public/ASpawner.h
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ASpawner.generated.h"

UCLASS(BlueprintType, Blueprintable)
class EXAMPLE_API ASpawner : public AActor
{
    GENERATED_BODY()

public:
    ASpawner();

    virtual void BeginPlay() override;

    /** Спавн одного объекта */
    UFUNCTION(BlueprintCallable)
    void SpawnObject();

    /** Класс объекта для спавна */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawn Settings")
    TSubclassOf<AActor> SpawnClass;

    /** Множественный спавн по таймеру */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawn Settings")
    bool bMultipleSpawn = false;

    /** Интервал между спавнами */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawn Settings", meta = (EditCondition = "bMultipleSpawn", ClampMin = "0.01"))
    float SpawnInterval = 5.0f;

    /** Максимальное количество объектов */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawn Settings", meta = (EditCondition = "bMultipleSpawn", ClampMin = "1"))
    int32 MaxSpawnCount = 5;

    /** Радиус разброса спавна */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawn Settings", meta = (ClampMin = "0.0"))
    float SpawnRadius = 100.0f;

    /** Выравнивание по нормали поверхности */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawn Settings")
    bool bAlignToSurface = true;

    /** Высота начала трассировки */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawn Settings", meta = (ClampMin = "0.0"))
    float TraceHeightAbove = 1000.0f;

protected:
    /** Таймер для интервального спавна */
    FTimerHandle SpawnTimerHandle;

    /** Массив спавненных объектов */
    UPROPERTY(Transient)
    TArray<TWeakObjectPtr<AActor>> SpawnedActors;

    /** Обработчик уничтожения */
    UFUNCTION()
    void OnSpawnedActorDestroyed(AActor* DestroyedActor);

    /** Очистка массива от уничтоженных */
    void CleanUpDestroyedActors();
};
