#import "PQLivesStore.h"

static NSString *const kKey = @"puzzlequest.lives";

@implementation PQLivesStore

+ (instancetype)sharedStore
{
    static PQLivesStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQLivesStore alloc] init];
    });
    return shared;
}

- (NSInteger)count
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setCount:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
